# Role Name #
A brief description of the role goes here.

# Requirements #
Any pre-requisites that may not be covered by Ansible itself or the role should be mentioned here. For instance, if the role uses the EC2 module, it may be a good idea to mention in this section that the boto package is required.

# Role Variables #
```
admin_email: ""
postfix_myhostname: ""
postfix_relayhost: ""
```

# Dependencies #
A list of other roles hosted on Galaxy should go here, plus any details in regards to parameters that may need to be set for other roles, or variables that are used from other roles.

# Example Playbook #
````
- hosts: servers
  roles:
     - { role: postfix-satellite, become: yes }
```

# Amazon SES
  *  To send production email through Amazon SES, you can use the Simple Mail Transfer Protocol (SMTP) [interface](https://docs.aws.amazon.com/ses/latest/DeveloperGuide/send-email-smtp.html) or the Amazon SES API.
  * To set up a [STARTTLS](https://docs.aws.amazon.com/ses/latest/DeveloperGuide/smtp-connect.html) connection, the SMTP client connects to the Amazon SES SMTP endpoint on port 25, 587, or 2587
  * Getting SES [credentials](https://docs.aws.amazon.com/en_pv/ses/latest/DeveloperGuide/smtp-credentials.html)
  * Configure [postfix](https://docs.aws.amazon.com/ses/latest/DeveloperGuide/postfix.html)
  *  Before you can send email using Amazon SES, you have to [verify](https://docs.aws.amazon.com/ses/latest/DeveloperGuide/regions.html)] that you own the email address or domain that you plan to send from.
  * Verify your [addresses and domains](https://docs.aws.amazon.com/ses/latest/DeveloperGuide/verify-addresses-and-domains.html)
  * Verify your [domain](https://docs.aws.amazon.com/ses/latest/DeveloperGuide/verify-domain-procedure.html)
  * Configure [DKIM](https://docs.aws.amazon.com/ses/latest/DeveloperGuide/easy-dkim.html)
  * Configure [MAIL FROM](https://docs.aws.amazon.com/ses/latest/DeveloperGuide/mail-from.html)
  * To help [prevent](https://docs.aws.amazon.com/ses/latest/DeveloperGuide/request-production-access.html) fraud and abuse, and to help protect your reputation as a sender, we apply certain restrictions to new Amazon SES accounts.

# License #
BSD

# Author Information #
[Real Time Enterprises Inc.](http://www.real-time.com),
[Bob Tanner](https://github.com/basictheprogram)
