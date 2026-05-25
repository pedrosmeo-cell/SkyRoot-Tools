from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
import uuid
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Dicionário de conversão unificado
STORES_MAP = {
    'amazon': 'Amazon Global',
    'amazon-br': 'Amazon Brasil',
    'aliexpress-pt-es': 'AliExpress Global',
    'aliexpress-br': 'AliExpress Brasil'
}


# --- FUNÇÕES DE DADOS ---
def load_data():
    if not os.path.exists('data'): os.makedirs('data')
    if not os.path.exists(app.config['DATA_FILE']):
        with open(app.config['DATA_FILE'], 'w', encoding='utf-8') as f:
            json.dump({"products": []}, f)
    with open(app.config['DATA_FILE'], 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except:
            data = {"products": []}

    # Migração automática: Garante que todos os produtos recebem um ID único fixo
    updated = False
    for p in data.get('products', []):
        if 'id' not in p:
            p['id'] = str(uuid.uuid4())
            updated = True
    if updated:
        save_data(data)

    return data


def save_data(data):
    with open(app.config['DATA_FILE'], 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# --- FILTROS ---
@app.template_filter('slugify')
def slugify_filter(s):
    if not s: return ""
    s = s.replace("(", "").replace(")", "").replace("/", "-")
    return s.lower().replace(" ", "-").replace("&", "")


# --- RESOLUÇÃO DO CAMINHO DA IMAGEM ---
def fix_image_path(affiliate, raw_image):
    """Limpa o nome da imagem e devolve o caminho correto da pasta."""
    img = str(raw_image).strip().replace("AMAZON/", "").replace("ALIEXPRESS/", "")
    if "Amazon" in str(affiliate):
        return f"AMAZON/{img}"
    else:
        return f"ALIEXPRESS/{img}"


# --- ROTAS ---
@app.route('/')
def index():
    data = load_data()
    all_products = data.get('products', [])
    featured = [p for p in all_products if p.get('featured')]

    for p in featured:
        p['folder_path'] = fix_image_path(p.get('affiliate'), p.get('image') or p.get('image_url'))

    return render_template('index.html', products=list(reversed(featured))[:12])


@app.route('/produtos/<store_name>')
def produtos(store_name):
    data = load_data()
    all_products = data.get('products', [])
    slug = store_name.strip().lower()

    if slug not in STORES_MAP:
        return render_template('produtos.html', products=[], category=store_name.upper())

    target_brand = STORES_MAP[slug].strip().lower()

    # FILTRAGEM ROBUSTA: Compara tudo limpo e em minúsculas para listar sempre os produtos
    store_products = [
        p for p in all_products
        if str(p.get('affiliate', '')).strip().lower() == target_brand
    ]

    cat_filter = request.args.get('cat')
    if cat_filter:
        store_products = [p for p in store_products if
                          str(p.get('category', '')).strip().lower() == cat_filter.strip().lower()]

    for p in store_products:
        p['folder_path'] = fix_image_path(p.get('affiliate'), p.get('image') or p.get('image_url'))

    return render_template('produtos.html', products=store_products, category=STORES_MAP[slug].upper())


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        if request.method == 'POST':
            if request.form.get('password') == app.config['ADMIN_PASSWORD']:
                session['logged_in'] = True
                return redirect(url_for('dashboard'))
            return render_template('login.html', error="Acesso Negado")
        return render_template('login.html')

    if request.method == 'POST':
        affiliate = request.form.get('affiliate').strip()
        img_raw = request.form.get('image_url').strip()

        # Insere automaticamente o nome da pasta no JSON de forma limpa
        final_image_path = fix_image_path(affiliate, img_raw)

        new_product = {
            "id": str(uuid.uuid4()),
            "affiliate": affiliate,
            "name": request.form.get('name').strip(),
            "price": request.form.get('price').strip(),
            "category": request.form.get('category').strip(),
            "image": final_image_path,
            "link": request.form.get('link').strip(),
            "featured": True if request.form.get('featured') == 'yes' else False
        }
        data = load_data()
        data['products'].append(new_product)
        save_data(data)
        return redirect(url_for('dashboard'))
    return render_template('admin.html')


@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    data = load_data()
    all_products = data.get('products', [])
    stores_data = {}

    for p in all_products:
        brand = str(p.get('affiliate') or 'Outros').strip()
        cat = str(p.get('category') or 'Geral').strip()

        p['folder_path'] = fix_image_path(brand, p.get('image') or p.get('image_url'))

        if brand not in stores_data: stores_data[brand] = {}
        if cat not in stores_data[brand]: stores_data[brand][cat] = []
        stores_data[brand][cat].append(p)

    return render_template('dashboard.html', stores_data=stores_data)


@app.route('/edit/<product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if not session.get('logged_in'): return redirect(url_for('admin'))

    data = load_data()
    product = next((p for p in data['products'] if p.get('id') == product_id), None)

    if not product:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        affiliate = request.form.get('affiliate').strip()
        img_raw = request.form.get('image_url').strip()

        product["affiliate"] = affiliate
        product["name"] = request.form.get('name').strip()
        product["price"] = request.form.get('price').strip()
        product["category"] = request.form.get('category').strip()
        product["image"] = fix_image_path(affiliate, img_raw)
        product["link"] = request.form.get('link').strip()
        product["featured"] = True if request.form.get('featured') == 'yes' else False

        save_data(data)
        return redirect(url_for('dashboard'))

    p_copy = product.copy()
    p_copy['image'] = str(p_copy.get('image', '')).replace("AMAZON/", "").replace("ALIEXPRESS/", "").strip()

    return render_template('edit.html', p=p_copy, product_id=product_id)


@app.route('/delete_product/<product_id>')
def delete_product(product_id):
    if not session.get('logged_in'): return redirect(url_for('admin'))
    data = load_data()
    data['products'] = [p for p in data['products'] if p.get('id') != product_id]
    save_data(data)
    return redirect(url_for('dashboard'))


@app.route('/toggle_featured/<product_id>')
def toggle_featured(product_id):
    if not session.get('logged_in'): return redirect(url_for('admin'))
    data = load_data()
    product = next((p for p in data['products'] if p.get('id') == product_id), None)
    if product:
        product['featured'] = not product.get('featured', False)
        save_data(data)
    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/guia')
def guia(): return render_template('guia.html')


@app.route('/parceiros')
def parceiros(): return render_template('parceiros.html')


@app.route('/termos')
def termos(): return render_template('legal.html', title="Termos e Condições")


@app.route('/privacidade')
def privacidade(): return render_template('legal.html', title="Política de Privacidade")


@app.route('/litigios')
def litigios(): return render_template('legal.html', title="Resolução de Litígios")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
