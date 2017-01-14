import requests
import os

print('Loading function')


# for aws lambda execution
def lambda_handler(event, context):
    message = event['Records'][0]['Sns']['Message']
    print("SNS Message: " + message)
    ErrorWebhook().main(message)
    return "done"


class ErrorWebhook:

    recipients = os.environ['DISCORD_RECIPIENTS']
    webhook = os.environ['DISCORD_WEBHOOK']

    def main(self, message):
        payload = {"content": "%s %s" % (self.recipients, message)}
        response = requests.post(self.webhook, json=payload)
        print(response.status_code)

# for local execution
if __name__ == "__main__":
    ErrorWebhook().main("a message")
