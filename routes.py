import csv
import io
import datetime
from urllib.parse import urljoin, urlparse
from flask import render_template, redirect, url_for, flash, request, jsonify, Response, current_app
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import desc

from app import db
from models import User, EmailTemplate, Campaign, Target, EducationalContent
from forms import LoginForm, RegistrationForm, EmailTemplateForm, CampaignForm, TargetForm, EducationalContentForm
from email_utils import send_phishing_email

def register_routes(app):
    
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('login.html', title='Login', form=LoginForm())
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user is None or not user.check_password(form.password.data):
                flash('Invalid username or password', 'danger')
                return redirect(url_for('login'))
            
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('dashboard')
            return redirect(next_page)
        
        return render_template('login.html', title='Login', form=form)
    
    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('login'))
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            if User.query.count() == 0:  # First user becomes admin
                user.is_admin = True
            
            db.session.add(user)
            db.session.commit()
            flash('Registration successful. You can now log in.', 'success')
            return redirect(url_for('login'))
        
        return render_template('register.html', title='Register', form=form)
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Get recent campaigns
        recent_campaigns = Campaign.query.filter_by(user_id=current_user.id).order_by(desc(Campaign.created_at)).limit(5).all()
        
        # Get campaign statistics
        total_campaigns = Campaign.query.filter_by(user_id=current_user.id).count()
        active_campaigns = Campaign.query.filter_by(user_id=current_user.id, status='in_progress').count()
        total_targets = 0
        total_sent = 0
        total_opened = 0
        total_clicked = 0
        
        all_campaigns = Campaign.query.filter_by(user_id=current_user.id).all()
        for campaign in all_campaigns:
            campaign_targets = Target.query.filter_by(campaign_id=campaign.id).count()
            total_targets += campaign_targets
            total_sent += campaign.sent_count
            total_opened += campaign.opened_count
            total_clicked += campaign.clicked_count
        
        # Calculate rates
        click_rate = round((total_clicked / total_sent * 100) if total_sent > 0 else 0, 2)
        open_rate = round((total_opened / total_sent * 100) if total_sent > 0 else 0, 2)
        
        return render_template('dashboard.html', 
                              title='Dashboard',
                              recent_campaigns=recent_campaigns,
                              total_campaigns=total_campaigns,
                              active_campaigns=active_campaigns,
                              total_targets=total_targets,
                              total_sent=total_sent,
                              total_opened=total_opened,
                              total_clicked=total_clicked,
                              click_rate=click_rate,
                              open_rate=open_rate)
    
    @app.route('/campaigns')
    @login_required
    def campaigns():
        campaigns = Campaign.query.filter_by(user_id=current_user.id).order_by(desc(Campaign.created_at)).all()
        return render_template('campaigns.html', title='Campaigns', campaigns=campaigns)
    
    @app.route('/campaigns/new', methods=['GET', 'POST'])
    @login_required
    def new_campaign():
        form = CampaignForm()
        templates = EmailTemplate.query.filter_by(user_id=current_user.id).all()
        form.template_id.choices = [(t.id, t.name) for t in templates]
        
        if form.validate_on_submit():
            campaign = Campaign(
                name=form.name.data,
                description=form.description.data,
                template_id=form.template_id.data,
                user_id=current_user.id,
                status='draft'
            )
            if form.schedule.data:
                campaign.scheduled_time = form.scheduled_time.data
                campaign.status = 'scheduled'
            
            db.session.add(campaign)
            db.session.commit()
            flash('Campaign created successfully!', 'success')
            return redirect(url_for('campaign_detail', campaign_id=campaign.id))
        
        return render_template('campaign_detail.html', title='New Campaign', form=form, campaign=None)
    
    @app.route('/campaigns/<int:campaign_id>', methods=['GET', 'POST'])
    @login_required
    def campaign_detail(campaign_id):
        campaign = Campaign.query.get_or_404(campaign_id)
        
        # Ensure user owns the campaign
        if campaign.user_id != current_user.id:
            flash('Access denied to this campaign', 'danger')
            return redirect(url_for('campaigns'))
        
        form = CampaignForm(obj=campaign)
        templates = EmailTemplate.query.filter_by(user_id=current_user.id).all()
        form.template_id.choices = [(t.id, t.name) for t in templates]
        
        if form.validate_on_submit():
            campaign.name = form.name.data
            campaign.description = form.description.data
            campaign.template_id = form.template_id.data
            
            if form.schedule.data and not campaign.scheduled_time:
                campaign.scheduled_time = form.scheduled_time.data
                campaign.status = 'scheduled'
            
            db.session.commit()
            flash('Campaign updated successfully!', 'success')
            return redirect(url_for('campaign_detail', campaign_id=campaign.id))
        
        # Get targets for this campaign
        targets = Target.query.filter_by(campaign_id=campaign.id).all()
        target_form = TargetForm()
        
        return render_template('campaign_detail.html', 
                              title=campaign.name, 
                              campaign=campaign, 
                              form=form, 
                              targets=targets,
                              target_form=target_form)
    
    @app.route('/campaigns/<int:campaign_id>/targets/add', methods=['POST'])
    @login_required
    def add_target(campaign_id):
        campaign = Campaign.query.get_or_404(campaign_id)
        
        # Ensure user owns the campaign
        if campaign.user_id != current_user.id:
            flash('Access denied to this campaign', 'danger')
            return redirect(url_for('campaigns'))
        
        form = TargetForm()
        if form.validate_on_submit():
            target = Target(
                campaign_id=campaign.id,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                email=form.email.data
            )
            db.session.add(target)
            db.session.commit()
            flash('Target added successfully!', 'success')
        
        return redirect(url_for('campaign_detail', campaign_id=campaign.id))
    
    @app.route('/campaigns/<int:campaign_id>/targets/import', methods=['POST'])
    @login_required
    def import_targets(campaign_id):
        campaign = Campaign.query.get_or_404(campaign_id)
        
        # Ensure user owns the campaign
        if campaign.user_id != current_user.id:
            flash('Access denied to this campaign', 'danger')
            return redirect(url_for('campaigns'))
        
        if 'csv_file' not in request.files:
            flash('No file provided', 'danger')
            return redirect(url_for('campaign_detail', campaign_id=campaign.id))
        
        file = request.files['csv_file']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(url_for('campaign_detail', campaign_id=campaign.id))
        
        if not file.filename.endswith('.csv'):
            flash('Only CSV files are allowed', 'danger')
            return redirect(url_for('campaign_detail', campaign_id=campaign.id))
        
        try:
            # Read CSV file
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_reader = csv.reader(stream)
            
            # Skip header row
            header = next(csv_reader)
            required_fields = ['first_name', 'last_name', 'email']
            
            # Normalize header field names
            header = [h.lower().strip() for h in header]
            
            # Check if all required fields are present
            for field in required_fields:
                if field not in header:
                    flash(f'CSV file is missing required field: {field}', 'danger')
                    return redirect(url_for('campaign_detail', campaign_id=campaign.id))
            
            # Get indices for required fields
            first_name_idx = header.index('first_name')
            last_name_idx = header.index('last_name')
            email_idx = header.index('email')
            
            # Process rows
            target_count = 0
            for row in csv_reader:
                if len(row) >= 3:  # Ensure row has enough fields
                    target = Target(
                        campaign_id=campaign.id,
                        first_name=row[first_name_idx],
                        last_name=row[last_name_idx],
                        email=row[email_idx]
                    )
                    db.session.add(target)
                    target_count += 1
            
            db.session.commit()
            flash(f'Successfully imported {target_count} targets!', 'success')
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error importing targets: {str(e)}', 'danger')
        
        return redirect(url_for('campaign_detail', campaign_id=campaign.id))
    
    @app.route('/campaigns/<int:campaign_id>/launch', methods=['POST'])
    @login_required
    def launch_campaign(campaign_id):
        campaign = Campaign.query.get_or_404(campaign_id)
        
        # Ensure user owns the campaign
        if campaign.user_id != current_user.id:
            flash('Access denied to this campaign', 'danger')
            return redirect(url_for('campaigns'))
        
        # Check if there are targets
        targets = Target.query.filter_by(campaign_id=campaign.id).all()
        if not targets:
            flash('Cannot launch campaign without targets', 'danger')
            return redirect(url_for('campaign_detail', campaign_id=campaign.id))
        
        # Check if template exists
        template = EmailTemplate.query.get(campaign.template_id)
        if not template:
            flash('Email template not found', 'danger')
            return redirect(url_for('campaign_detail', campaign_id=campaign.id))
        
        # Check Gmail settings
        if not current_app.config['MAIL_USERNAME'] or not current_app.config['MAIL_PASSWORD']:
            flash('Gmail credentials are not configured correctly. Please check your GMAIL_USER and GMAIL_PASSWORD environment variables.', 'danger')
            return redirect(url_for('campaign_detail', campaign_id=campaign.id))
        
        # Update campaign status
        campaign.status = 'in_progress'
        db.session.commit()
        
        # Schedule immediate sending or use the scheduled time
        if not campaign.scheduled_time or campaign.scheduled_time <= datetime.datetime.utcnow():
            # Send emails now
            send_count = 0
            for target in targets:
                if not target.email_sent:
                    try:
                        send_phishing_email(current_app, template, target)
                        target.email_sent = True
                        target.email_sent_at = datetime.datetime.utcnow()
                        db.session.commit()
                        send_count += 1
                    except Exception as e:
                        current_app.logger.error(f"Error sending email to {target.email}: {str(e)}")
                        flash(f'Error sending email to {target.email}', 'warning')
            
            if send_count > 0:
                flash(f'Successfully sent {send_count} phishing emails!', 'success')
            else:
                flash('No emails were sent', 'warning')
        else:
            flash(f'Campaign scheduled to run at {campaign.scheduled_time}', 'info')
        
        return redirect(url_for('campaign_detail', campaign_id=campaign.id))
    
    @app.route('/templates')
    @login_required
    def templates():
        templates = EmailTemplate.query.filter_by(user_id=current_user.id).order_by(desc(EmailTemplate.created_at)).all()
        return render_template('templates.html', title='Email Templates', templates=templates)
    
    @app.route('/templates/new', methods=['GET', 'POST'])
    @login_required
    def new_template():
        form = EmailTemplateForm()
        
        if form.validate_on_submit():
            template = EmailTemplate(
                name=form.name.data,
                subject=form.subject.data,
                sender_name=form.sender_name.data,
                sender_email=form.sender_email.data,
                content=form.content.data,
                user_id=current_user.id
            )
            db.session.add(template)
            db.session.commit()
            flash('Template created successfully!', 'success')
            return redirect(url_for('templates'))
        
        return render_template('template_editor.html', title='New Template', form=form, template=None)
    
    @app.route('/templates/<int:template_id>', methods=['GET', 'POST'])
    @login_required
    def edit_template(template_id):
        template = EmailTemplate.query.get_or_404(template_id)
        
        # Ensure user owns the template
        if template.user_id != current_user.id:
            flash('Access denied to this template', 'danger')
            return redirect(url_for('templates'))
        
        form = EmailTemplateForm(obj=template)
        
        if form.validate_on_submit():
            template.name = form.name.data
            template.subject = form.subject.data
            template.sender_name = form.sender_name.data
            template.sender_email = form.sender_email.data
            template.content = form.content.data
            db.session.commit()
            flash('Template updated successfully!', 'success')
            return redirect(url_for('templates'))
        
        return render_template('template_editor.html', title='Edit Template', form=form, template=template)
    
    @app.route('/reports')
    @login_required
    def reports():
        campaigns = Campaign.query.filter_by(user_id=current_user.id).all()
        return render_template('reports.html', title='Reports', campaigns=campaigns)
    
    @app.route('/reports/<int:campaign_id>')
    @login_required
    def campaign_report(campaign_id):
        campaign = Campaign.query.get_or_404(campaign_id)
        
        # Ensure user owns the campaign
        if campaign.user_id != current_user.id:
            flash('Access denied to this campaign', 'danger')
            return redirect(url_for('reports'))
        
        targets = Target.query.filter_by(campaign_id=campaign.id).all()
        
        # Calculate statistics
        total_targets = len(targets)
        emails_sent = sum(1 for t in targets if t.email_sent)
        emails_opened = sum(1 for t in targets if t.email_opened)
        links_clicked = sum(1 for t in targets if t.link_clicked)
        
        # Calculate rates
        open_rate = round((emails_opened / emails_sent * 100) if emails_sent > 0 else 0, 2)
        click_rate = round((links_clicked / emails_sent * 100) if emails_sent > 0 else 0, 2)
        
        return render_template('campaign_report.html', 
                              title=f'Report: {campaign.name}',
                              campaign=campaign,
                              targets=targets,
                              total_targets=total_targets,
                              emails_sent=emails_sent,
                              emails_opened=emails_opened,
                              links_clicked=links_clicked,
                              open_rate=open_rate,
                              click_rate=click_rate)
    
    @app.route('/reports/<int:campaign_id>/export', methods=['POST'])
    @login_required
    def export_report(campaign_id):
        campaign = Campaign.query.get_or_404(campaign_id)
        
        # Ensure user owns the campaign
        if campaign.user_id != current_user.id:
            flash('Access denied to this campaign', 'danger')
            return redirect(url_for('reports'))
        
        targets = Target.query.filter_by(campaign_id=campaign.id).all()
        
        # Prepare CSV data
        csv_data = io.StringIO()
        csv_writer = csv.writer(csv_data)
        
        # Write header row
        csv_writer.writerow([
            'First Name', 
            'Last Name', 
            'Email', 
            'Email Sent', 
            'Sent Time',
            'Email Opened', 
            'Opened Time',
            'Link Clicked', 
            'Clicked Time',
            'IP Address',
            'User Agent'
        ])
        
        # Write data rows
        for target in targets:
            csv_writer.writerow([
                target.first_name,
                target.last_name,
                target.email,
                'Yes' if target.email_sent else 'No',
                target.email_sent_at.strftime('%Y-%m-%d %H:%M:%S') if target.email_sent_at else '',
                'Yes' if target.email_opened else 'No',
                target.email_opened_at.strftime('%Y-%m-%d %H:%M:%S') if target.email_opened_at else '',
                'Yes' if target.link_clicked else 'No',
                target.link_clicked_at.strftime('%Y-%m-%d %H:%M:%S') if target.link_clicked_at else '',
                target.ip_address or '',
                target.user_agent or ''
            ])
        
        # Return CSV file
        response = Response(
            csv_data.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=phishing_report_{campaign.name}_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )
        return response
    
    @app.route('/track/<tracking_id>')
    def track_open(tracking_id):
        """Track email opens via a 1x1 transparent pixel"""
        target = Target.query.filter_by(tracking_id=tracking_id).first()
        
        if target and not target.email_opened:
            target.email_opened = True
            target.email_opened_at = datetime.datetime.utcnow()
            target.ip_address = request.remote_addr
            target.user_agent = request.user_agent.string
            db.session.commit()
        
        # Return a 1x1 transparent GIF
        transparent_pixel = bytes.fromhex('47494638396101000100800000000000ffffff21f90401000000002c00000000010001000002024401003b')
        return Response(transparent_pixel, mimetype='image/gif')
    
    @app.route('/click/<tracking_id>')
    def landing(tracking_id):
        """Handle phishing link clicks and redirect to educational content"""
        target = Target.query.filter_by(tracking_id=tracking_id).first()
        
        if target and not target.link_clicked:
            target.link_clicked = True
            target.link_clicked_at = datetime.datetime.utcnow()
            target.ip_address = request.remote_addr
            target.user_agent = request.user_agent.string
            db.session.commit()
        
        # Select random educational content to display
        content = EducationalContent.query.order_by(db.func.random()).first()
        
        # If no content exists, create a default one
        if not content:
            content = EducationalContent(
                title="Phishing Awareness",
                content="You've just encountered a simulated phishing attempt as part of your organization's security awareness training.",
                tips="Always verify the sender's email address. Be cautious with unexpected attachments. Don't click on suspicious links."
            )
            db.session.add(content)
            db.session.commit()
        
        return render_template('educational.html', content=content, target=target)
    
    @app.route('/educational')
    @login_required
    def manage_educational():
        """Manage educational content shown to users who click on phishing links"""
        content_list = EducationalContent.query.all()
        form = EducationalContentForm()
        
        if form.validate_on_submit():
            content = EducationalContent(
                title=form.title.data,
                content=form.content.data,
                tips=form.tips.data
            )
            db.session.add(content)
            db.session.commit()
            flash('Educational content created successfully!', 'success')
            return redirect(url_for('manage_educational'))
        
        return render_template('educational_manage.html', 
                              title='Educational Content',
                              content_list=content_list,
                              form=form)
    
    @app.route('/feedback/<tracking_id>', methods=['POST'])
    def submit_feedback(tracking_id):
        """Handle feedback from users who fell for the phishing simulation"""
        target = Target.query.filter_by(tracking_id=tracking_id).first()
        
        if not target:
            return jsonify({'success': False, 'message': 'Invalid tracking ID'})
        
        # Mark feedback as completed
        target.feedback_completed = True
        db.session.commit()
        
        return jsonify({'success': True})
    
    @app.context_processor
    def utility_processor():
        """Helper functions available in templates"""
        def tracking_url(target):
            """Generate a tracking URL for a target"""
            app_url = current_app.config['APP_URL']
            return urljoin(app_url, f'/click/{target.tracking_id}')
        
        def pixel_url(target):
            """Generate a tracking pixel URL for a target"""
            app_url = current_app.config['APP_URL']
            return urljoin(app_url, f'/track/{target.tracking_id}')
        
        return dict(tracking_url=tracking_url, pixel_url=pixel_url)