
import streamlit as st
from supabase import create_client
from datetime import datetime, timezone

st.set_page_config(
    page_title="Akademik Kitaplığım",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Akademik Kitaplığım")

# SUPABASE BAĞLANTISI

try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_PUBLISHABLE_KEY"]
except (KeyError, FileNotFoundError):
    st.error("Supabase bağlantısı yapılandırılmadı.")
    st.stop()

if "sb" not in st.session_state:
    st.session_state.sb = create_client(url, key)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

sb = st.session_state.sb

# KULLANICI GİRİŞİ

if not st.session_state.logged_in:
    st.info("Bu katalog kişisel kullanıma özeldir.")

    with st.form("login"):
        email = st.text_input("E-posta")
        password = st.text_input("Şifre", type="password")
        submit = st.form_submit_button(
            "Giriş yap", use_container_width=True
        )

    if submit:
        try:
            response = sb.auth.sign_in_with_password({
                "email": email.strip(),
                "password": password
            })

            if response.user and response.session:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Giriş yapılamadı.")

                except Exception as e:
            st.error(f"Giriş hatası: {type(e).__name__}")
            st.code(str(e))

    st.stop()

try:
    user_response = sb.auth.get_user()

    if not user_response.user:
        raise ValueError("Oturum bulunamadı")

    user_id = user_response.user.id

except Exception:
    st.session_state.logged_in = False
    st.warning("Oturumunuz sona erdi. Yeniden giriş yapın.")
    st.stop()

# YARDIMCI FONKSİYONLAR

def temizle(value):
    return str(value).strip() if value is not None else ""

def bos_ise_null(value):
    return temizle(value) or None

def turkce_normalize(value):
    return temizle(value).replace(
        "İ", "i"
    ).replace("I", "ı").casefold()

def kitaplari_getir():
    kitaplar = []
    baslangic = 0
    sayfa_boyutu = 500

    while True:
        result = (
            sb.table("kitaplar")
            .select("*")
            .eq("kullanici_id", user_id)
            .order("baslik")
            .order("id")
            .range(
                baslangic,
                baslangic + sayfa_boyutu - 1
            )
            .execute()
        )

        grup = result.data or []
        kitaplar.extend(grup)

        if len(grup) < sayfa_boyutu:
            break

        baslangic += sayfa_boyutu

    return kitaplar

def kitap_filtrele(kitaplar, sorgu, alanlar):
    kelimeler = turkce_normalize(sorgu).split()

    if not kelimeler:
        return kitaplar

    return [
        kitap for kitap in kitaplar
        if all(
            kelime in turkce_normalize(
                " ".join(
                    temizle(kitap.get(alan))
                    for alan in alanlar
                )
            )
            for kelime in kelimeler
        )
    ]

def kitap_etiketi(kitap):
    parcalar = [
        temizle(kitap.get("baslik")) or "Başlıksız",
        temizle(kitap.get("yazar")) or "Yazar belirtilmemiş"
    ]

    for alan in ["yayinevi", "yayin_yili", "cilt", "sayi"]:
        if kitap.get(alan):
            parcalar.append(temizle(kitap[alan]))

    if kitap.get("excel_sira_no") is not None:
        parcalar.append(
            f"Excel: {kitap['excel_sira_no']}"
        )
    else:
        parcalar.append(
            f"Kayıt: {str(kitap['id'])[:8]}"
        )

    return " — ".join(parcalar)

# KİTAP FORMU

def kitap_formu(kitap=None):

    kitap = kitap or {}
    duzenleme = bool(kitap.get("id"))

    durumlar = [
        "Kaydedildi",
        "Tarandı",
        "Tarandı ve ihraç edildi"
    ]

    mevcut_durum = kitap.get("durum") or "Kaydedildi"

    if mevcut_durum not in durumlar:
        durumlar.append(mevcut_durum)

    form_key = (
        f"edit_{kitap['id']}"
        if duzenleme else "add_book"
    )

    with st.form(form_key):

        baslik = st.text_input(
            "Kitap / yayın başlığı *",
            value=temizle(kitap.get("baslik"))
        )

        yazar = st.text_input(
            "Yazar",
            value=temizle(kitap.get("yazar"))
        )

        isbn = st.text_input(
            "ISBN",
            value=temizle(kitap.get("isbn"))
        )

        yayin_turu = st.text_input(
            "Yayın türü",
            value=temizle(kitap.get("yayin_turu")),
            placeholder="Kitap, dergi, makale vb."
        )

        yayinevi = st.text_input(
            "Yayınevi",
            value=temizle(kitap.get("yayinevi"))
        )

        yayin_yeri = st.text_input(
            "Yayın yeri",
            value=temizle(kitap.get("yayin_yeri"))
        )

        yayin_yili = st.number_input(
            "Yayın yılı (bilinmiyorsa 0)",
            min_value=0,
            max_value=2200,
            value=int(kitap.get("yayin_yili") or 0),
            step=1
        )

        baski = st.text_input(
            "Baskı",
            value=temizle(kitap.get("baski"))
        )

        cilt = st.text_input(
            "Cilt",
            value=temizle(kitap.get("cilt"))
        )

        sayi = st.text_input(
            "Sayı",
            value=temizle(kitap.get("sayi"))
        )

        raf_no = st.text_input(
            "Raf numarası",
            value=temizle(kitap.get("raf_no"))
        )

        durum = st.selectbox(
            "Durum",
            durumlar,
            index=durumlar.index(mevcut_durum)
        )

        with st.expander("Diğer bibliyografik bilgiler"):

            doi = st.text_input(
                "DOI",
                value=temizle(kitap.get("doi"))
            )

            kaynak_yayin = st.text_input(
                "Kaynak yayın",
                value=temizle(kitap.get("kaynak_yayin"))
            )

            sayfa_araligi = st.text_input(
                "Sayfa aralığı",
                value=temizle(kitap.get("sayfa_araligi"))
            )

        icindekiler = st.text_area(
            "İçindekiler",
            value=temizle(kitap.get("icindekiler")),
            height=250
        )

        sozcuk_dizini = st.text_area(
            "Sözcük dizini",
            value=temizle(kitap.get("sozcuk_dizini")),
            height=150
        )

        anahtar_kelimeler = st.text_input(
            "Anahtar kelimeler",
            value=temizle(kitap.get("anahtar_kelimeler"))
        )

        notlar = st.text_area(
            "Kişisel notlar",
            value=temizle(kitap.get("notlar")),
            height=120
        )

        submitted = st.form_submit_button(
            "Değişiklikleri kaydet"
            if duzenleme else "Kitabı kaydet",
            use_container_width=True
        )

    if not submitted:
        return

    if not baslik.strip():
        st.warning("Yayın başlığı boş bırakılamaz.")
        return

    veri = {
        "baslik": baslik.strip(),
        "yazar": bos_ise_null(yazar),
        "isbn": bos_ise_null(isbn),
        "yayin_turu": bos_ise_null(yayin_turu),
        "yayinevi": bos_ise_null(yayinevi),
        "yayin_yeri": bos_ise_null(yayin_yeri),
        "yayin_yili": int(yayin_yili) if yayin_yili else None,
        "baski": bos_ise_null(baski),
        "cilt": bos_ise_null(cilt),
        "sayi": bos_ise_null(sayi),
        "raf_no": bos_ise_null(raf_no),
        "durum": durum,
        "doi": bos_ise_null(doi),
        "kaynak_yayin": bos_ise_null(kaynak_yayin),
        "sayfa_araligi": bos_ise_null(sayfa_araligi),
        "icindekiler": bos_ise_null(icindekiler),
        "sozcuk_dizini": bos_ise_null(sozcuk_dizini),
        "anahtar_kelimeler": bos_ise_null(anahtar_kelimeler),
        "notlar": bos_ise_null(notlar),
        "guncellenme_tarihi": datetime.now(
            timezone.utc
        ).isoformat()
    }

    try:
        if duzenleme:
            result = (
                sb.table("kitaplar")
                .update(veri)
                .eq("id", kitap["id"])
                .eq("kullanici_id", user_id)
                .execute()
            )

            if not result.data:
                st.error("Kayıt güncellenemedi.")
                return

            st.success("Kitap bilgileri güncellendi.")

        else:
            veri["kullanici_id"] = user_id

            result = (
                sb.table("kitaplar")
                .insert(veri)
                .execute()
            )

            if not result.data:
                st.error("Kayıt doğrulanamadı.")
                return

            st.success("Kitap başarıyla kaydedildi.")

    except Exception as e:
        st.error("Kayıt işlemi tamamlanamadı.")
        st.code(str(e))

# MENÜ

with st.sidebar:

    st.success("Oturum açık")

    page = st.radio(
        "Menü",
        [
            "Kitap ara",
            "Kitap ekle",
            "Kitap düzenle"
        ]
    )

    st.divider()

    if st.button("Çıkış yap"):
        try:
            sb.auth.sign_out()
        finally:
            st.session_state.clear()
            st.rerun()

    st.caption("Akademik Kitaplığım — Sürüm 2.0")

# KİTAP ARAMA

if page == "Kitap ara":

    query = st.text_input(
        "Kitap adı, yazar, ISBN veya içindekilerde ara",
        placeholder="Örn. Osmanlı eğitim"
    )

    try:
        kitaplar = kitaplari_getir()
    except Exception:
        st.error("Kitaplar okunamadı.")
        st.stop()

    st.caption(
        f"Kitaplığınızdaki toplam yayın: {len(kitaplar)}"
    )

    kitaplar = kitap_filtrele(
        kitaplar,
        query,
        [
            "baslik",
            "yazar",
            "isbn",
            "yayinevi",
            "icindekiler",
            "sozcuk_dizini",
            "anahtar_kelimeler"
        ]
    )

    st.write(f"**{len(kitaplar)} yayın bulundu.**")

    sayfa_boyutu = 20

    sayfa_sayisi = max(
        1,
        (len(kitaplar) + sayfa_boyutu - 1)
        // sayfa_boyutu
    )

    sayfa = st.selectbox(
        "Sonuç sayfası",
        range(1, sayfa_sayisi + 1)
    )

    baslangic = (sayfa - 1) * sayfa_boyutu

    for b in kitaplar[
        baslangic:baslangic + sayfa_boyutu
    ]:

        with st.expander(kitap_etiketi(b)):

            alanlar = {
                "ISBN": "isbn",
                "Yayın türü": "yayin_turu",
                "Yayınevi": "yayinevi",
                "Yayın yeri": "yayin_yeri",
                "Yayın yılı": "yayin_yili",
                "Baskı": "baski",
                "Cilt": "cilt",
                "Sayı": "sayi",
                "Raf": "raf_no",
                "Durum": "durum",
                "DOI": "doi",
                "Kaynak yayın": "kaynak_yayin",
                "Sayfa aralığı": "sayfa_araligi"
            }

            for etiket, alan in alanlar.items():
                if b.get(alan):
                    st.write(
                        f"**{etiket}:** {b[alan]}"
                    )

            for etiket, alan in [
                ("İçindekiler", "icindekiler"),
                ("Sözcük dizini", "sozcuk_dizini"),
                ("Anahtar kelimeler", "anahtar_kelimeler"),
                ("Kişisel notlar", "notlar")
            ]:
                if b.get(alan):
                    st.text_area(
                        etiket,
                        value=b[alan],
                        height=160,
                        disabled=True,
                        key=f"{alan}_{b['id']}"
                    )

# KİTAP EKLEME

elif page == "Kitap ekle":

    st.subheader("Yeni yayın ekle")
    kitap_formu()

# KİTAP DÜZENLEME

elif page == "Kitap düzenle":

    st.subheader("Mevcut yayını düzenle")

    query = st.text_input(
        "Düzenlenecek yayını ara",
        placeholder="Kitap adı, yazar veya ISBN"
    )

    if not query.strip():
        st.info("Düzenlemek istediğiniz yayını arayın.")
        st.stop()

    try:
        kitaplar = kitaplari_getir()
    except Exception:
        st.error("Kitaplar okunamadı.")
        st.stop()

    kitaplar = kitap_filtrele(
        kitaplar,
        query,
        [
            "baslik",
            "yazar",
            "isbn",
            "yayinevi",
            "excel_sira_no"
        ]
    )

    if not kitaplar:
        st.warning("Aramanıza uygun yayın bulunamadı.")
        st.stop()

    st.write(f"**{len(kitaplar)} yayın bulundu.**")

    kitap_sozlugu = {
        b["id"]: b for b in kitaplar
    }

    secilen_id = st.selectbox(
        "Düzenlenecek yayını seçin",
        options=list(kitap_sozlugu.keys()),
        format_func=lambda x: kitap_etiketi(
            kitap_sozlugu[x]
        )
    )

    kitap_formu(kitap_sozlugu[secilen_id])
