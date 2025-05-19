#import os
#from flask import Flask, redirect, render_template, send_from_directory

#BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#REACT_HOST_DIR = "https://remap.itot.jp/MFtest/react-host"

#app = Flask(__name__, static_folder=os.path.join(REACT_HOST_DIR, 'static'), static_url_path='/static')

#@app.route('/')
#def index():
#    return redirect("/hazard")

# 画像用のルート（catch-allより前に定義）
#@app.route('/images/<path:filename>')
#def serve_images(filename):
#    images_dir = os.path.join(REACT_HOST_DIR, "images")
#    return send_from_directory(images_dir, filename)

# catch-all ルート
#@app.route('/<path:path>')
#def catch_all(path):
    # ここで渡すデータの内容を切り替える
#    props = {
#        "center": {"lat": 35.35096595843089, "lng": 139.45595465135227},
#        "facilityName": "藤沢本町",
#        "hazardType": "浸水" #津波
#    }
    
#    return render_template('CommonPage.htm', page_title="Module Federation Sample", props=props)

#if __name__ == '__main__':
#    app.run(debug=True, port=5000)