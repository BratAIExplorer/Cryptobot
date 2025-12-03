"""
Alert Manager Module
Handles multi-channel notifications (Desktop, Email, Telegram)
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from plyer import notification
import requests
from typing import Dict, List
import config

class AlertManager:
    """Manage alerts across multiple channels"""
    
    def __init__(self):
        """Initialize alert manager with configured channels"""
        # Telegram configuration
        self.telegram_token = config.TELEGRAM_BOT_TOKEN
        self.telegram_chat_id = config.TELEGRAM_CHAT_ID
    
    def send_desktop_notification(self, title: str, message: str, timeout: int = 10):
        """
        Send desktop notification (Windows toast notification)
        
        Args:
            title: Notification title
            message: Notification message
            timeout: Duration in seconds
        """
        if not config.ENABLE_DESKTOP_NOTIFICATIONS:
            return
        
        try:
            notification.notify(
                title=title,
                message=message,
                app_name='Luno Portfolio Monitor',
                timeout=timeout
            )
            print(f"✓ Desktop notification sent: {title}")
        except Exception as e:
            print(f"✗ Desktop notification failed: {e}")
    
    def send_email_alert(self, subject: str, body: str, is_html: bool = False):
        """
        Send email alert via Gmail
        
        Args:
            subject: Email subject
            body: Email body (plain text or HTML)
            is_html: Whether body is HTML formatted
        """
        if not config.ENABLE_EMAIL_ALERTS:
            return
        
        if not config.GMAIL_ADDRESS or not config.GMAIL_APP_PASSWORD:
            print("✗ Email alerts not configured")
            return
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = config.GMAIL_ADDRESS
            msg['To'] = config.GMAIL_ADDRESS  # Send to self
            msg['Subject'] = subject
            
            # Attach body
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Send via Gmail SMTP
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(config.GMAIL_ADDRESS, config.GMAIL_APP_PASSWORD)
                server.send_message(msg)
            
            print(f"✓ Email sent: {subject}")
        except Exception as e:
            print(f"✗ Email failed: {e}")
    
    def send_telegram_alert(self, message: str):
        """
        Send Telegram alert (free WhatsApp alternative)
        
        Args:
            message: Message text (supports HTML formatting)
        """
        if not config.ENABLE_TELEGRAM_ALERTS:
            return
        
        if not self.telegram_token or not self.telegram_chat_id:
            print("✗ Telegram alerts not configured")
            return
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            print(f"✓ Telegram message sent")
        except Exception as e:
            print(f"✗ Telegram failed: {e}")
    
    def send_profit_target_alert(self, alert_data: Dict):
        """
        Send alert when profit target is reached
        
        Args:
            alert_data: Dictionary with alert information
        """
        coin = alert_data['coin']
        profit_pct = alert_data['profit_pct']
        current_price = alert_data['current_price']
        target_price = alert_data['target_price']
        
        # Desktop notification
        self.send_desktop_notification(
            title=f"🎯 {coin} Profit Target Reached!",
            message=f"{profit_pct}% profit! Current: RM{current_price:,.2f}"
        )
        
        # Email alert
        email_body = f"""
        <h2>🎯 Profit Target Reached!</h2>
        <p><strong>Cryptocurrency:</strong> {coin}</p>
        <p><strong>Profit Target:</strong> {profit_pct}%</p>
        <p><strong>Target Price:</strong> RM {target_price:,.2f}</p>
        <p><strong>Current Price:</strong> RM {current_price:,.2f}</p>
        <p><strong>Time:</strong> {alert_data.get('timestamp', 'Now')}</p>
        
        <p style="color: green; font-weight: bold;">
        Consider reviewing your position and deciding whether to sell.
        </p>
        """
        
        self.send_email_alert(
            subject=f"🎯 {coin} reached {profit_pct}% profit target!",
            body=email_body,
            is_html=True
        )
        
        # Telegram alert
        telegram_msg = f"""
🎯 <b>Profit Target Reached!</b>

<b>Coin:</b> {coin}
<b>Profit:</b> {profit_pct}%
<b>Target:</b> RM {target_price:,.2f}
<b>Current:</b> RM {current_price:,.2f}

✅ Consider selling to lock in profits!
        """
        
        self.send_telegram_alert(telegram_msg)
    
    def send_price_drop_alert(self, alert_data: Dict):
        """
        Send alert for significant price drop
        
        Args:
            alert_data: Dictionary with alert information
        """
        coin = alert_data['coin']
        drop_pct = alert_data['drop_pct']
        current_price = alert_data['current_price']
        previous_price = alert_data['previous_price']
        
        # Desktop notification
        self.send_desktop_notification(
            title=f"⚠️ {coin} Price Drop Alert!",
            message=f"Dropped {drop_pct:.2f}%! Now: RM{current_price:,.2f}"
        )
        
        # Email alert
        email_body = f"""
        <h2>⚠️ Significant Price Drop Detected!</h2>
        <p><strong>Cryptocurrency:</strong> {coin}</p>
        <p><strong>Price Drop:</strong> {drop_pct:.2f}%</p>
        <p><strong>Previous Price:</strong> RM {previous_price:,.2f}</p>
        <p><strong>Current Price:</strong> RM {current_price:,.2f}</p>
        
        <p style="color: orange; font-weight: bold;">
        Monitor the situation closely. This could be a temporary dip or start of a trend.
        </p>
        """
        
        self.send_email_alert(
            subject=f"⚠️ {coin} dropped {drop_pct:.2f}%",
            body=email_body,
            is_html=True
        )
        
        # Telegram alert
        telegram_msg = f"""
⚠️ <b>Price Drop Alert!</b>

<b>Coin:</b> {coin}
<b>Drop:</b> {drop_pct:.2f}%
<b>From:</b> RM {previous_price:,.2f}
<b>To:</b> RM {current_price:,.2f}

📉 Monitor closely!
        """
        
        self.send_telegram_alert(telegram_msg)
    
    def send_daily_summary(self, portfolio_data: Dict):
        """
        Send daily portfolio summary
        
        Args:
            portfolio_data: Dictionary with portfolio metrics
        """
        total_value = portfolio_data.get('total_value', 0)
        total_profit_pct = portfolio_data.get('total_profit_pct', 0)
        holdings = portfolio_data.get('holdings', [])
        
        # Build summary
        summary_lines = [f"<b>{h['coin']}</b>: RM {h['value']:,.2f} ({h['profit_pct']:+.2f}%)" 
                        for h in holdings[:5]]  # Top 5
        
        telegram_msg = f"""
📊 <b>Daily Portfolio Summary</b>

<b>Total Value:</b> RM {total_value:,.2f}
<b>Overall P/L:</b> {total_profit_pct:+.2f}%

<b>Top Holdings:</b>
{chr(10).join(summary_lines)}

💡 Keep holding until targets are reached!
        """
        
        self.send_telegram_alert(telegram_msg)
        
        # Also send email version
        email_body = f"""
        <h2>📊 Daily Portfolio Summary</h2>
        <p><strong>Total Portfolio Value:</strong> RM {total_value:,.2f}</p>
        <p><strong>Overall Profit/Loss:</strong> {total_profit_pct:+.2f}%</p>
        
        <h3>Holdings:</h3>
        <ul>
        {''.join([f"<li><strong>{h['coin']}</strong>: RM {h['value']:,.2f} ({h['profit_pct']:+.2f}%)</li>" for h in holdings])}
        </ul>
        """
        
        self.send_email_alert(
            subject=f"📊 Daily Portfolio Summary - {total_profit_pct:+.2f}%",
            body=email_body,
            is_html=True
        )
    
    def send_test_alerts(self):
        """Send test alerts to verify all channels are working"""
        print("\nSending test alerts...")
        
        # Test desktop
        if config.ENABLE_DESKTOP_NOTIFICATIONS:
            self.send_desktop_notification(
                "Luno Monitor Test",
                "Desktop notifications are working! ✓"
            )
        
        # Test email
        if config.ENABLE_EMAIL_ALERTS:
            self.send_email_alert(
                "Luno Monitor Test",
                "Email alerts are working! ✓"
            )
        
        # Test Telegram
        if config.ENABLE_TELEGRAM_ALERTS:
            self.send_telegram_alert(
                "🤖 <b>Luno Monitor Test</b>\n\nTelegram alerts are working! ✓"
            )
        
        print("✓ Test alerts sent")


if __name__ == "__main__":
    # Test alert manager
    print("Testing Alert Manager...")
    
    manager = AlertManager()
    manager.send_test_alerts()
