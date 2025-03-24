import qrcode

img = qrcode.make('https://upskill-ods.herokuapp.com/')
img.save('HerokuQRCode.jpg')
