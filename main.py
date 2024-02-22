from bson import ObjectId
from flask import Flask, render_template, request, redirect, session
import pymongo
app = Flask(__name__)
app.secret_key = "your_secret_key"  # Oturum anahtarını güvenli bir şekilde belirleyin.

# MongoDB'ye bağlantı kurulur
client = pymongo.MongoClient()
db = client["eduSozlukDBN"]

def get_sequence(seq_name):
    return db.counters.find_one_and_update(filter={"_id": seq_name}, update={"$inc": {"seq": 1}}, upsert=True)["seq"]


@app.route('/')
def home_page():
    basliklar = list(db["basliklar"].find({}).sort("_id",-1))
    print("ilk başlık:", basliklar[0])
    yazilar = list(db["yazilar"].find({"baslik_id": basliklar[0]["_id"]}).sort("_id",-1).skip(100).limit(20))
    return render_template("baslik-detay.html", aktif_baslik=basliklar[0], basliklar=basliklar, yazilar=yazilar)


@app.route('/uye-ol', methods=["GET", "POST"])
def uye_ol():
    if request.method == 'GET':
        return render_template("uye-ol.html")
    else:
        # Formdan gelen verileri al
        email = request.form["email"]
        sifre = request.form["sifre"]
        adsoyad = request.form["adsoyad"]



        # Verileri collection'a ekle
        db["kullanicilar"].insert_one({
            "_id": email,
            "sifre": sifre,
            "adsoyad": adsoyad
        })

        return redirect("/giris", 302)

@app.route('/giris', methods=["GET", "POST"])
def giris():
    if request.method == 'GET':
        return render_template("giris.html")
    else:
        # Formdan gelen verileri al
        email = request.form["email"]
        sifre = request.form["sifre"]

        kullanici = db["kullanicilar"].find_one({"_id": email})
        print("kullanici:",kullanici)
        if kullanici and kullanici["sifre"] == sifre:
            # Giriş başarılı, oturum bilgilerini sakla
            session['kullanici'] = kullanici
            return redirect("/", 302)
        else:
            return "Kullanıcı bulunamadı ya da şifre geçersiz"

@app.route('/cikis')
def cikis():
    # Oturumu temizle ve ana sayfaya yönlendir
    session.pop('kullanici', None)
    return redirect("/", 302)

# Yeni eklenen route
@app.route('/baslik/<baslik_id>/sayfa/<sayfa_no>')
def baslik_detay(baslik_id,sayfa_no):
    sayfalama_adet=5
    atlanacak_kayit = (int(sayfa_no) - 1) * sayfalama_adet
    if request.method == 'GET':
        basliklar = list(db["basliklar"].find({}).sort("_id",-1).limit(20))
        aktif_baslik = db["basliklar"].find_one({"_id": int(baslik_id)})
        yazilar = list(db["yazilar"].find({"baslik_id": int(baslik_id)}).sort("_id",-1).skip(atlanacak_kayit).limit(sayfalama_adet))
        return render_template("baslik-detay.html", aktif_baslik=aktif_baslik, basliklar=basliklar, yazilar=yazilar,sayfa_no=int(sayfa_no))

@app.route('/yazi-ekle', methods=["POST"])
def yazi_ekle():
    if request.method == 'POST':
        baslik_id = request.form["baslik_id"]
        db["yazilar"].insert_one({
            "_id": get_sequence("yazilar"),
            "baslik_id": int(baslik_id),
            "yazi": request.form["yeni_yazi"]
        })
        return redirect("/baslik/"+baslik_id, 302)

@app.route('/yazi-olustur', methods=["GET"])
def yazi_olustur():
    for i in range(300):
        if request.method == 'GET':
            baslik_id = 1
            db["yazilar"].insert_one({
                "_id": get_sequence("yazilar"),
                "baslik_id": baslik_id,
                "yazi": f"3000 yazı {i}"
            })

    return "okey"

@app.route('/yazi-sil', methods=["POST"])
def yazi_sil():
    if request.method == 'POST':
        baslik_id = request.form["baslik_id"]
        yazi_id = request.form['yazi_id']
        myquery = {"_id": int(yazi_id)}
        db["yazilar"].delete_one(myquery)

        return redirect("/baslik/"+baslik_id, 302)

@app.route('/yazi-guncelle', methods=["POST"])
def yazi_guncelle():
    if request.method == 'POST':
        baslik_id = request.form["baslik_id"]
        yazi_id = request.form["yazi_id"]
        yeni_yazi = request.form["yeni_yazi"]

        if not yazi_id:  # Eğer yazi_id değeri boş ise
            return "Yazı ID boş olamaz!"

        my_query = {"_id": int(yazi_id)}

        yenisi = {"$set": {"yazi": yeni_yazi}}
        # Belgeyi güncelle
        db["yazilar"].update_one(my_query, yenisi)

        return redirect("/baslik/"+baslik_id, 302)
    else:
        return "Yalnızca POST istekleri kabul edilir."

@app.route('/baslik-ekle', methods=["POST"])
def baslik_ekle():
    if request.method == 'POST':
        # Formdan gelen veriyi al
        baslik = request.form["baslik"]

        # Yeni başlığı veritabanına ekleyin
        yeni_baslik_id = get_sequence("basliklar")
        db["basliklar"].insert_one({
            "_id": yeni_baslik_id,
            "baslik": baslik
        })

        return redirect("/baslik/{}".format(yeni_baslik_id), 302)
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)