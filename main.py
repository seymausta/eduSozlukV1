from bson import ObjectId
from flask import Flask, render_template, request, redirect, session
import pymongo
app = Flask(__name__)
app.secret_key = "your_secret_key"  # Oturum anahtarını güvenli bir şekilde belirleyin.

# MongoDB'ye bağlantı kurulur
client = pymongo.MongoClient()
db = client["eduSozlukDBN"]

# Kullanıcı adını alacak basit bir fonksiyon
def get_current_user():
    # Session'da "email" anahtarına sahip bir kullanıcı var mı kontrol et
    user_email = session.get("email")
    if user_email:
        kullanici = db["kullanicilar"].find_one({"_id": user_email})
        return kullanici["adsoyad"] if kullanici else None
    return None

# Yazıları çekmek için fonksiyon
def get_yazilar(baslik_id):
    # "yazilar" koleksiyonundan belirli bir başlığa ait yazıları çek
    yazilar = db["yazilar"].find({"baslik_id": int(baslik_id)})
    return list(yazilar)

@app.route('/')
def home_page():
    # Kullanıcı adını al
    current_user = get_current_user()

    # Başlıkları al
    basliklar = get_basliklar()

    return render_template("home.html",current_user=current_user,basliklar=basliklar)

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
        if kullanici and kullanici["sifre"] == sifre:
            # Giriş başarılı, oturum bilgilerini sakla
            session["email"] = email
            return redirect("/", 302)
        else:
            return "Kullanıcı bulunamadı ya da şifre geçersiz"

@app.route('/cikis')
def cikis():
    # Oturumu temizle ve ana sayfaya yönlendir
    session.clear()
    return redirect("/", 302)

def get_basliklar():
    # "basliklar" koleksiyonundaki tüm başlıkları çek
    basliklar = db["basliklar"].find({}, {"_id": 0, "baslik": 1})
    return [baslik["baslik"] for baslik in basliklar]

# Yeni eklenen route
@app.route('/baslik-detay/<baslik_id>')
def baslik_detay(baslik_id):
    # Başlıkları al
    basliklar = get_basliklar()
    # Başlığı al
    baslik = db["basliklar"].find_one({"_id": int(baslik_id)})
    if baslik:
        # Başlığa ait yazıları al
        yazilar = get_yazilar(baslik_id)
        return render_template("baslik-detay.html", baslik=baslik, yazilar=yazilar,basliklar=basliklar)
    else:
        return "Başlık bulunamadı"



if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)