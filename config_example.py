import web

db = web.database(dbn='sqlite', db='blog.db')
password_minlen = 6 # Min length of passwords   
forced_delay = 0.5 # Artificial delay to slow down brute-force attacks

# SMTP EMail settings for password-reset
web.config.smtp_server = 'smtp.gmail.com' #http://webpy.org/cookbook/sendmail_using_gmail
web.config.smtp_port = 587
web.config.smtp_username = 'you@gmail.com'
web.config.smtp_password = 'your_password'
web.config.smtp_starttls = True
