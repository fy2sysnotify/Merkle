requestCounter += 1

print('Fifth request endpoint - get list of all sandboxes including deleted')
# Make request to url for listing all ODS - Sandbox On Demand including deleted
logger.debug('Fifth request endpoint - get list of all sandboxes including deleted')

try:
    sandboxListWithDeleted = requests.get(
        "https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes?include_deleted=true",
        headers=headers, verify=False).json()
except Exception as conn_error:
    logger.error(conn_error)
    logger.debug('Failed to get Sandbox list including deleted')
    email_recipient = 'konstantin.yanev@isobar.com'
    email_subject = 'Failed to get Sandbox lists including deleted in cron job - isobar-web-ods-usage-report_sfcc'
    email_text = 'Failed to get Sandbox lists including deleted in cron job - isobar-web-ods-usage-report_sfcc.'
    email_attachment = str(Path.cwd() / f'isobar-web-ods-usage-report_sfcc_{todayIs}.log')
    send_email(email_recipient, email_subject, email_text, email_attachment)
    raise

logger.debug(f'Fifth request endpoint answer is {sandboxListWithDeleted}')
print(sandboxListWithDeleted)

rowNumber = 1
columnNumber = 0
list2fill = []
for i in sandboxListWithDeleted['data']:
    realm = i['realm']
    realmName = ''
    if realm == 'aaay':  # Smenyash ID-to mezhdu kavichkite s tova na klienta, koito iskash da reportvash. ID-to se vzima ot https://wiki.isobarsystems.com/display/SUPTEAM/Local+POD+time+-+Notifications
        realmName = 'web'  # Smenyash imeto mezhdu kavichkite s tova na klienta, koito iskash da reportvash.
        sandboxId = i['id']

        requestCounter += 1

        print('Sixth request endpoint - get Sandbox usage since 2021-03-01 with deleted')
        # Make request with sandboxIDs to get Sandbox usage since 2021-03-01 with deleted
        logger.debug('Sixth request endpoint - Sandbox usage since 2021-03-01 with deleted')

        try:
            sandboxUsageWithDeletedSince2021_03_01 = requests.get(
                f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandboxId}/usage?from=2021-03-01",
                headers=headers).json()
        except Exception as conn_error:
            logger.error(conn_error)
            logger.debug('Failed to get Sandbox usage from sixth request endpoint')
            email_recipient = 'konstantin.yanev@isobar.com'
            email_subject = 'Failed to get Sandbox usage with deleted since 21.03.01. in cron job - isobar-web-ods-usage-report_sfcc'
            email_text = 'Failed to get Sandbox usage with deleted since 21.01.03. in cron job - isobar-web-ods-usage-report_sfcc. Check the attached logs'
            email_attachment = str(Path.cwd() / f'isobar-web-ods-usage-report_sfcc_{todayIs}.log')
            send_email(email_recipient, email_subject, email_text, email_attachment)

        logger.debug(f'Sixth request endpoint answer is {sandboxUsageWithDeletedSince2021_03_01}')

        print(sandboxUsageWithDeletedSince2021_03_01)

        totalCreditsWithDeleted = 0
        minutesUpWithDeleted210301 = sandboxUsageWithDeletedSince2021_03_01['data']['minutesUp']
        minutesDownWithDeleted210301 = sandboxUsageWithDeletedSince2021_03_01['data']['minutesDown']
        creditsSpentWithDeleted = minutesUpWithDeleted210301 + (minutesDownWithDeleted210301 * 0.3)
        totalCreditsWithDeleted = totalCreditsWithDeleted + creditsSpentWithDeleted