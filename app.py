import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Akademik Kitaplığım", page_icon="📚", layout="wide")
st.title("📚 Akademik Kitaplığım")

try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_PUBLISHABLE_KEY"]
except (KeyError, FileNotFoundError):
    st.error("Supabase bağlantısı henüz yapılandırılmadı. Streamlit Secrets ayarlarına SUPABASE_URL ve SUPABASE_PUBLISHABLE_KEY ekleyin.")
    st.stop()

if "sb" not in st.session_state:
    st.session_state.sb = create_client(url, key)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
sb = st.session_state.sb

if not st.session_state.logged_in:
    st.info("Bu katalog kişisel kullanıma özeldir. Devam etmek için giriş yapın.")
    with st.form("login"):
        email = st.text_input("E-posta")
        password = st.text_input("Şifre", type="password")
        submit = st.form_submit_button("Giriş yap", use_container_width=True)
    if submit:
        try:
            response = sb.auth.sign_in_with_password({"email": email.strip(), "password": password})
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
except Exception:
    st.session_state.logged_in = False
    st.warning("Oturumunuz sona erdi. Lütfen yeniden giriş yapın.")
    st.stop()

with st.sidebar:
    st.success("Oturum açık")
    if st.button("Çıkış yap"):
        try:
            sb.auth.sign_out()
        finally:
            st.session_state.logged_in = False
            st.session_state.pop("sb", None)
            st.rerun()
    page = st.radio("Menü", ["Kitap ara", "Kitap ekle"])

if page == "Kitap ara":
    query = st.text_input("Kitap adı, yazar, ISBN veya içindekilerde ara", placeholder="Örn. Osmanlı'da eğitim")
    st.caption("İlk sürüm kelime araması yapar. Anlamsal arama daha sonra eklenecektir.")
    try:
        result = sb.table("kitaplar").select("id,baslik,yazar,isbn,yayinevi,yayin_yili,raf_no,durum,icindekiler").order("baslik").limit(1000).execute()
        books = result.data or []
    except Exception:
        st.error("Kitaplar okunamadı. Supabase Data API ayarlarını, tablo izinlerini ve RLS kurallarını kontrol edin.")
        st.stop()
    if query.strip():
        words = query.casefold().split()
        books = [b for b in books if all(w in " ".join(str(b.get(k) or "") for k in ["baslik", "yazar", "isbn", "yayinevi", "icindekiler"]).casefold() for w in words)]
    st.write(f"**{len(books)} kitap bulundu** (ilk 1000 kayıt üzerinden)")
    for b in books:
        with st.expander(f"{b.get('baslik') or 'Başlıksız'} — {b.get('yazar') or 'Yazar belirtilmemiş'}"):
            st.write(f"**ISBN:** {b.get('isbn') or '—'}  |  **Yayınevi:** {b.get('yayinevi') or '—'}  |  **Yıl:** {b.get('yayin_yili') or '—'}")
            st.write(f"**Raf:** {b.get('raf_no') or '—'}  |  **Durum:** {b.get('durum') or '—'}")
            if b.get("icindekiler"):
                st.text_area("İçindekiler", value=b["icindekiler"], height=160, disabled=True, key=f"toc_{b['id']}")
else:
    with st.form("add_book", clear_on_submit=True):
        title = st.text_input("Kitap başlığı *")
        author = st.text_input("Yazar")
        isbn = st.text_input("ISBN")
        publisher = st.text_input("Yayınevi")
        year = st.number_input("Yayın yılı (bilinmiyorsa 0)", min_value=0, max_value=2200, value=0)
        shelf = st.text_input("Raf numarası")
        status = st.selectbox("Durum", ["Kaydedildi", "Tarandı", "Tarandı ve ihraç edildi"])
        contents = st.text_area("İçindekiler metni (isteğe bağlı)", height=180)
        submitted = st.form_submit_button("Kitabı kaydet")
    if submitted:
        if not title.strip():
            st.warning("Kitap başlığını girin.")
        else:
            try:
                sb.table("kitaplar").insert({
                    "baslik": title.strip(), "yazar": author.strip() or None,
                    "isbn": isbn.strip() or None, "yayinevi": publisher.strip() or None,
                    "yayin_yili": int(year) if year else None,
                    "raf_no": shelf.strip() or None, "durum": status,
                    "icindekiler": contents.strip() or None,
                }).execute()
                st.success("Kitap kaydedildi.")
            except Exception:
                st.error("Kitap kaydedilemedi. Oturum ve Supabase tablo izinlerini kontrol edin.")
