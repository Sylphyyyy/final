import csv
import io
from datetime import datetime, timezone

from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, session, make_response
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import update

from app import db
from app.models import User, Procurement, Item, AvailableStock

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')


def _login_required():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return None


@settings_bp.route('/', methods=['GET'])
def settings():
    redirect_result = _login_required()
    if redirect_result:
        return redirect_result

    user = db.session.get(User, session['user_id'])
    if not user:
        session.clear()
        flash('User not found.', 'danger')
        return redirect(url_for('auth.login'))

    return render_template('auth/settings.html', user=user)


@settings_bp.route('/', methods=['POST'])
def update_settings():
    redirect_result = _login_required()
    if redirect_result:
        return redirect_result

    user = db.session.get(User, session['user_id'])
    if not user:
        session.clear()
        flash('User not found.', 'danger')
        return redirect(url_for('auth.login'))

    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip().lower() or None
    email_notifications = request.form.get('email_notifications') == 'on'
    warning_days = request.form.get('expiration_warning_days', type=int)
    status_filter = request.form.get('default_status_filter', 'Ongoing')
    two_factor = request.form.get('two_factor_enabled') == 'on'

    if not username:
        flash('Username is required.', 'danger')
        return redirect(url_for('settings.settings'))

    if username != user.username:
        existing = User.query.filter_by(username=username).first()
        if existing:
            flash('Username is already taken.', 'danger')
            return redirect(url_for('settings.settings'))
        user.username = username

    if email is not None:
        user.email = email

    user.email_notifications = email_notifications
    user.expiration_warning_days = warning_days if warning_days and warning_days > 0 else 30
    user.default_status_filter = status_filter
    user.two_factor_enabled = two_factor

    db.session.commit()
    session['username'] = user.username
    flash('Settings updated successfully.', 'success')
    return redirect(url_for('settings.settings'))


@settings_bp.route('/change-password', methods=['POST'])
def change_password():
    redirect_result = _login_required()
    if redirect_result:
        return redirect_result

    user = db.session.get(User, session['user_id'])
    if not user:
        session.clear()
        flash('User not found.', 'danger')
        return redirect(url_for('auth.login'))

    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not user.check_password(current_password):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('settings.settings'))

    if len(new_password) < 12 or len(new_password) > 128:
        flash('New password must be between 12 and 128 characters.', 'danger')
        return redirect(url_for('settings.settings'))

    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('settings.settings'))

    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    flash('Password changed successfully.', 'success')
    return redirect(url_for('settings.settings'))


@settings_bp.route('/logout-all', methods=['POST'])
def logout_all():
    redirect_result = _login_required()
    if redirect_result:
        return redirect_result

    session.clear()
    flash('Signed out of all sessions. Please log in again.', 'info')
    return redirect(url_for('auth.login'))


@settings_bp.route('/export-data', methods=['POST'])
def export_data():
    redirect_result = _login_required()
    if redirect_result:
        return redirect_result

    user = db.session.get(User, session['user_id'])
    if not user:
        session.clear()
        flash('User not found.', 'danger')
        return redirect(url_for('auth.login'))

    procurements = Procurement.query.all()
    items = Item.query.all()
    available_stock = AvailableStock.query.all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['=== PROCUREMENTS ==='])
    writer.writerow(['id', 'title', 'abc', 'pre_bid_date', 'place_of_bidding', 'municipality', 'agency', 'status', 'created_at'])
    for p in procurements:
        writer.writerow([p.id, p.title, p.abc, p.pre_bid_date, p.place_of_bidding, p.municipality, p.agency, p.status, p.created_at])

    writer.writerow([])
    writer.writerow(['=== ITEMS ==='])
    writer.writerow(['id', 'procurement_id', 'code', 'name', 'category', 'price', 'unit', 'target_qty', 'current_qty', 'expiration_date', 'delivery_checked'])
    for i in items:
        writer.writerow([i.id, i.procurement_id, i.code, i.name, i.category, i.price, i.unit, i.target_qty, i.current_qty, i.expiration_date, i.delivery_checked])

    writer.writerow([])
    writer.writerow(['=== AVAILABLE STOCK ==='])
    writer.writerow(['id', 'name', 'quantity', 'unit', 'expiration_date'])
    for s in available_stock:
        writer.writerow([s.id, s.name, s.quantity, s.unit, s.expiration_date])

    csv_content = output.getvalue()
    output.close()

    response = make_response(csv_content)
    response.headers['Content-Disposition'] = f'attachment; filename=inventory_export_{datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")}.csv'
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    return response


@settings_bp.route('/delete-account', methods=['POST'])
def delete_account():
    redirect_result = _login_required()
    if redirect_result:
        return redirect_result

    user = db.session.get(User, session['user_id'])
    if not user:
        session.clear()
        flash('User not found.', 'danger')
        return redirect(url_for('auth.login'))

    confirm_username = request.form.get('confirm_username', '').strip()
    if confirm_username != user.username:
        flash('Username confirmation does not match.', 'danger')
        return redirect(url_for('settings.settings'))

    db.session.delete(user)
    db.session.commit()
    session.clear()
    flash('Your account has been permanently deleted.', 'info')
    return redirect(url_for('auth.login'))
