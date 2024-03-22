from flask import Flask, render_template, request, redirect, url_for, flash
import os
import docx
from PyPDF2 import PdfReader
import spacy
from googlesearch import search

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

nlp = spacy.load('en_core_web_sm')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    text = ''
    for paragraph in doc.paragraphs:
        text += paragraph.text + '\n'  # Agregamos un salto de línea al final de cada párrafo
    return text

def extract_text_from_pdf(file_path):
    text = ''
    with open(file_path, 'rb') as f:
        reader = PdfReader(f)
        for page_num in range(len(reader.pages)):
            text += reader.pages[page_num].extract_text()
    return text

def analyze_cv(text):
    doc = nlp(text)
    skills = []
    entities = [ent.text for ent in doc.ents]
    skill_keywords = ['experience in', 'skills in', 'knowledge of', 'proficient in', 'familiar with', 'ability to']
    for sentence in doc.sents:
        for keyword in skill_keywords:
            if keyword in sentence.text.lower():
                start_index = sentence.text.lower().find(keyword) + len(keyword)
                end_index = sentence.text.find(',', start_index)
                if end_index == -1:
                    end_index = len(sentence.text)
                skill = sentence.text[start_index:end_index].strip()
                skills.append(skill)
    return entities, skills

def recommend_jobs(skills, location):
    jobs = []
    for skill in skills:
        query = f'jobs for {skill} in {location}'
        for result in search(query, num=5, stop=5, pause=2):
            jobs.append(result)
    return jobs

def improve_profile(skills):
    suggestions = []
    # Generar recomendaciones personalizadas basadas en las habilidades identificadas
    for skill in skills:
        suggestions.append(f'Considera obtener certificaciones adicionales en {skill}')
        suggestions.append(f'Únete a grupos y comunidades en línea relacionados con {skill}')
    return suggestions

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            flash('File uploaded successfully')
            
            # Preprocesamiento de CV
            if filename.endswith('.docx'):
                text = extract_text_from_docx(file_path)
            elif filename.endswith('.pdf'):
                text = extract_text_from_pdf(file_path)
            else:
                flash('Unsupported file format')
                return redirect(url_for('index'))

            # Análisis de CV
            entities, skills = analyze_cv(text)

            # Recomendación de vacantes
            location = "Bogotá, Colombia"  # Esto puede ser extraído del CV si se proporciona la información
            jobs = recommend_jobs(skills, location)

            # Mejora del perfil
            suggestions = improve_profile(skills)

            return render_template('results.html', entities=entities, skills=skills, jobs=jobs, suggestions=suggestions)

if __name__ == '__main__':
    app.run(debug=True)
