def send_email():
    import os
    import numberplate
    import mysql.connector
    import datetime
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders

    # Database setup
    a = mysql.connector.connect(host="localhost", user="root", passwd="root")
    b = a.cursor()
    b.execute("create database if not exists speed")
    b.execute("use speed")
    b.execute("create table if not exists details(lic_plate varchar(20) primary key, stud_name varchar(50), email varchar(50), warning int default 0, fine_rs int default 0)")
    a.commit()

    # Define a function to send emails with an attachment
    def send_email(to_email, subject, message, attachment_path):
        try:
            # Email configuration
            from_email = "your email"
            from_password = "your private pass key"

            # Setup the MIME
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject

            # Attach the message body
            msg.attach(MIMEText(message, 'plain'))

            # Attach the image file
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {os.path.basename(attachment_path)}",
                )
                msg.attach(part)

            # Create server connection
            server = smtplib.SMTP('smtp.gmail.com', 587)  # Replace with your SMTP server and port
            server.starttls()
            server.login(from_email, from_password)

            # Send the email
            server.sendmail(from_email, to_email, msg.as_string())

            # Terminate the SMTP session
            server.quit()

            print(f"Sent email to {to_email}")
        except Exception as e:
            print(f"Error sending email: {e}")

    # Process all images in the 'screenshots' folder
    screenshots_folder = "screenshots"
    for filename in os.listdir(screenshots_folder):
        if filename.endswith(".png") or filename.endswith(".jpg"):  # Only process image files
            image_path = os.path.join(screenshots_folder, filename)
            number = numberplate.plate_recognition(image_path)
            print(f"Recognized number plate: {number}")

            # Query the database
            sql = "SELECT * FROM details WHERE lic_plate = %s"
            b.execute(sql, (number,))
            data = b.fetchone()
            print(data)

            if data:  # Check if a record is found
                warnings = data[3]
                email = data[2]

                # Update warnings and fine based on logic
                if warnings >= 2:
                    warnings += 1
                    fine = data[4] + 200
                    sql = "UPDATE details SET warning = %s, fine_rs = %s WHERE lic_plate = %s"
                    b.execute(sql, (warnings, fine, number))
                    message = f"You have crossed the speed limit.\nWarning: {warnings}\nFine: Rs.{fine}"
                else:
                    warnings += 1
                    fine = data[4]
                    sql = "UPDATE details SET warning = %s WHERE lic_plate = %s"
                    b.execute(sql, (warnings, number))
                    message = f"You have crossed the speed limit. Warning: {warnings}"

                a.commit()

                # Send email notification with attachment
                if email:
                    send_email(email, "Speed Limit Violation Notice", message, image_path)
                else:
                    print("Email not found in database")
            else:
                print(f"License plate {number} not found in the database")

    # Close the database connection
    a.close()
