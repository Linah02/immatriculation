import logging
logger = logging.getLogger(__name__)
# from django.http import HttpResponse
from django.template.loader import render_to_string
# from weasyprint import HTML

# from django.http import HttpResponse
# from weasyprint import HTML

import pdfkit
from pdfkit import configuration
from django.http import HttpResponse
# from django.template.loader import render_to_string


import json
from django.shortcuts import render, redirect,get_object_or_404
from .models import VueTransactionsParQuitEtContribuable  # Assurez-vous d'importer le modèle
from .models import VueSommeParContribuableParAnnee  # Assurez-vous d'importer le modèle
from .models import VueRecouvrementsEtPaiementsParAnnee
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.http import JsonResponse
from datetime import datetime, timedelta
from django.db import connection
from django.contrib.auth.decorators import login_required
from .models import TransactionDetail
def acceuil(request):
    return render(request, 'acceuil/acceuil.html')  

def acceuilCte(request):
    return render(request, 'acceuil/acceuilCte.html')  

def test_acceuil(request):
    return render(request, 'acceuil/test.html')  


def home1(request):
    return render(request, 'myapp/home1.html')  

def discussion(request):
    return render(request, 'acceuil/message.html')  

def notification(request):
    return render(request, 'acceuil/notification.html')  


def chart(request):
    # Récupérer l'ID du contribuable connecté depuis la session
    id_contribuable = request.session.get('contribuable_id')

    # Vérifier si l'utilisateur est connecté
    if not id_contribuable:
        return redirect('login')  # Redirige vers la page de login si non connecté

    # Récupérer les données depuis la base de données
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT contribuable, annee, total_mnt_ver FROM vue_somme_par_contribuable_par_annee WHERE contribuable = %s",
            [id_contribuable]
        )
        rows = cursor.fetchall()

    # Conversion des valeurs Decimal en float pour faciliter l'affichage JSON
    sommes = [{'contribuable': row[0], 'annee': row[1], 'total_mnt_ver': float(row[2])} for row in rows]
    
    # Rendu de la page avec les données JSON
    return render(request, 'acceuil/transaction_chart.html', {'sommes': json.dumps(sommes)})


def chart_line(request):
    # Récupérer l'ID du contribuable connecté depuis la session
    id_contribuable = request.session.get('contribuable_id')

    # Vérifier si l'utilisateur est connecté
    if not id_contribuable:
        return redirect('login')  # Redirige vers la page de login si non connecté

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT contribuable, annee_recouvrement, total_recouvrement_annuel, total_paye_annuel
            FROM vue_recouvrements_et_paiements_par_annee
            WHERE contribuable = %s
            """,
            [id_contribuable]
        )
        rows = cursor.fetchall()

    # Structurer les données pour le graphique
    data_par_contribuable = {}
    for contribuable, annee, total_recouvrement, total_paye in rows:
        # Convertir les valeurs Decimal en float
        total_recouvrement = float(total_recouvrement) if total_recouvrement is not None else 0.0
        total_paye = float(total_paye) if total_paye is not None else 0.0

        if contribuable not in data_par_contribuable:
            data_par_contribuable[contribuable] = {
                'annees': [],
                'recouvrements': [],
                'paiements': []
            }
        data_par_contribuable[contribuable]['annees'].append(annee)
        data_par_contribuable[contribuable]['recouvrements'].append(total_recouvrement)
        data_par_contribuable[contribuable]['paiements'].append(total_paye)

    # Retourner les données sous forme JSON
    return render(request, 'acceuil/evolution_transaction.html', {
        'data': json.dumps(data_par_contribuable)
    })

def list_transaction(request):
    # Récupérer l'ID du contribuable connecté depuis la session
    id_contribuable = request.session.get('contribuable_id')

    # Vérifier si l'utilisateur est connecté
    if not id_contribuable:
        return redirect('login')  # Redirige vers la page de login si non connecté

    # Créer la requête SQL pour obtenir les transactions du contribuable connecté
    query = """
        SELECT *
        FROM vue_transactions_par_quit_et_contribuable
        WHERE contribuable = %s;
    """
    
    # Exécuter la requête SQL
    with connection.cursor() as cursor:
        cursor.execute(query, [id_contribuable])
        transactions = cursor.fetchall()
    
    # Retourner le rendu avec toutes les transactions
    return render(request, 'acceuil/liste_transaction.html', {'transactions': transactions})


def filtre_list_transaction(request, min_montant=None, max_montant=None):
    # Récupérer l'ID du contribuable connecté depuis la session
    id_contribuable = request.session.get('contribuable_id')

    # Vérifier si l'utilisateur est connecté
    if not id_contribuable:
        return redirect('login')  # Redirige vers la page de login si non connecté

    # Récupérer les montants min et max à partir des paramètres GET, uniquement si fournis et valides
    try:
        if 'min' in request.GET and request.GET.get('min').strip():
            min_montant = float(request.GET['min'])
        if 'max' in request.GET and request.GET.get('max').strip():
            max_montant = float(request.GET['max'])
    except ValueError:
        logger.error("Valeur de min ou max non valide. Filtrage désactivé.")

    logger.debug(f"Filtrage avec min={min_montant} et max={max_montant}")

    # Construction de la requête SQL sécurisée avec des paramètres
    query = """
        SELECT *
        FROM vue_transactions_par_quit_et_contribuable
        WHERE contribuable = %s
    """
    params = [id_contribuable]

    if min_montant is not None and max_montant is not None:
        query += " AND mont_ap BETWEEN %s AND %s"
        params.extend([min_montant, max_montant])
    elif min_montant is not None:
        query += " AND mont_ap >= %s"
        params.append(min_montant)
    elif max_montant is not None:
        query += " AND mont_ap <= %s"
        params.append(max_montant)

    logger.debug(f"Requête SQL : {query}")

    # Exécuter la requête SQL
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        transactions = cursor.fetchall()

    # Passer la requête SQL dans le contexte pour l'afficher dans le template
    context = {
        'transactions': transactions,
    }

    # Retourner le rendu avec les transactions filtrées
    return render(request, 'acceuil/liste_transaction.html', context)


def profil(request):
    id_contribuable = request.session.get('contribuable_id')

    # Vérifier si l'utilisateur est connecté
    if not id_contribuable:
        return redirect('login')  # Redirige vers la page de login si non connecté

    with connection.cursor() as cursor:
        # Exécutez une requête pour récupérer les informations du contribuable
        cursor.execute("SELECT * FROM myapp_contribuable WHERE id = %s", [id_contribuable])
        contribuable = cursor.fetchone()  # Récupérer la première ligne de résultats

    if contribuable:
        # Préparer les données pour le template
        contribuable_info = {
            'id': contribuable[0],  # Adaptez les indices selon votre structure de table
            'nom': contribuable[1],
            'prenom': contribuable[2],
            'email': contribuable[10],
            'contact': contribuable[8],
            'photo': contribuable[17],
            'propr_nif': contribuable[18],
            'cin':contribuable[6],
            'mot_de_passe': contribuable[13],
            # Ajoutez d'autres champs selon votre modèle
        }
    else:
        contribuable_info = {}  # Aucune information trouvée

    return render(request, 'myapp/profil.html', {'contribuable': contribuable_info})


def get_transaction_details(request, n_quit):
    # Récupérer l'ID du contribuable à partir de la session utilisateur
    id_contribuable = request.session.get('contribuable_id')

    # Vérifier si l'utilisateur est connecté
    if not id_contribuable:
        return redirect('login')  # Redirige vers la page de login si non connecté


    # Préparation de la requête SQL
    sql_query = """
        SELECT 
            contribuable, 
            n_quit, 
            date_paiement, 
            annee_de_paiement, 
            annee_recouvrement, 
            date_debut, 
            date_fin, 
            base, 
            mnt_ap, 
            nimp AS NIMP, 
            imp_detail, 
            numero, 
            impot, 
            sens, 
            logiciel,
            montant
        FROM 
            vue_detail_transactions_par_quit_et_contribuable 
        WHERE 
            contribuable = %s AND n_quit = %s;
    """

    # Exécuter la requête SQL
    with connection.cursor() as cursor:
        # Logger la requête
        logger.info("Exécution de la requête SQL : SELECT * FROM vue_detail_transactions_par_quit_et_contribuable WHERE contribuable = %d AND n_quit = '%s'", id_contribuable, n_quit)

        cursor.execute(sql_query, [id_contribuable, n_quit])  # Assurez-vous que n_quit est une chaîne
        
        # Récupérer tous les résultats
        transaction_details = cursor.fetchall()

    # Formater la requête pour l'afficher dans le template
    sql_query_formatted = f"SELECT contribuable, n_quit, date_paiement, annee_de_paiement, annee_recouvrement, date_debut, date_fin, base, mnt_ap, nimp AS NIMP, imp_detail, numero, impot, sens, logiciel FROM vue_detail_transactions_par_quit_et_contribuable WHERE contribuable = {id_contribuable} AND n_quit = '{n_quit}'"

    # Passer la requête et les résultats au template
    return render(request, 'acceuil/transaction_details.html', {
        'transaction_details': transaction_details,
        'sql_query': sql_query_formatted,
        'n_quit':n_quit  # Utilisation de la requête formatée
    })




def filtre_detail_transaction(request, n_quit):
    # Initialisation de variables pour les filtres
    min_montant = request.GET.get('min')
    max_montant = request.GET.get('max')
    date_min = request.GET.get('date_min')
    date_max = request.GET.get('date_max')
    
    # Créer la requête SQL avec les filtres
    query = """
        SELECT *
        FROM vue_detail_transactions_par_quit_et_contribuable
        WHERE n_quit = %s
    """
    params = [n_quit]
    
    # Ajouter des filtres pour le montant
    if min_montant:
        query += " AND montant >= %s"
        params.append(min_montant)
    if max_montant:
        query += " AND montant <= %s"
        params.append(max_montant)
    
    # Ajouter des filtres pour la date
    if date_min:
        query += " AND date_paiement >= %s"
        params.append(date_min)
    if date_max:
        query += " AND date_paiement <= %s"
        params.append(date_max)

    # Exécution de la requête SQL
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        transaction_details = cursor.fetchall()

    # Formater la requête pour affichage avec les valeurs réelles
    formatted_query = query % tuple(map(repr, params))  # Remplace les %s par les valeurs réelles
    
    # Passez les transaction_details sous le nom 'transaction_details' dans le contexte
    context = {
        'transaction_details': transaction_details,  # Assurez-vous que c'est 'transactions' et non 'transaction_details'
        'n_quit': n_quit,
        'query': formatted_query,  # Passer la requête formatée pour débogage
    }
    # Rendre la page avec les résultats filtrés
    return render(request, 'acceuil/transaction_details.html', context)


def export_transaction_pdf(request, n_quit):
    # Définir le contribuable pour la requête SQL
    id_contribuable = request.session.get('contribuable_id')

    # Vérifier si l'utilisateur est connecté
    if not id_contribuable:
        return redirect('login')  # Redirige vers la page de login si non connecté

    # Exécuter la requête SQL pour obtenir les détails de la transaction
    sql_query = """
        SELECT 
            contribuable, 
            n_quit, 
            date_paiement, 
            annee_de_paiement, 
            annee_recouvrement, 
            date_debut, 
            date_fin, 
            base, 
            mnt_ap, 
            nimp AS NIMP, 
            imp_detail, 
            numero, 
            impot, 
            sens, 
            logiciel,
            montant
        FROM 
            vue_detail_transactions_par_quit_et_contribuable 
        WHERE 
            contribuable = %s AND n_quit = %s;
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_query, [id_contribuable, n_quit])
        transaction_details = cursor.fetchall()  # Récupère les résultats sous forme de liste

    # Passer les résultats au template pour générer le HTML
    html_string = render_to_string('acceuil/pdf_template.html', {
        'transaction_details': transaction_details,
        'n_quit': n_quit,
    })

    # Configuration de pdfkit
    path_wkhtmltopdf = r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe'  # Mettez le bon chemin ici
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

    # Créer le PDF avec pdfkit
    pdf = pdfkit.from_string(html_string, False, configuration=config)

    # Retourner le PDF comme réponse
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="transaction_{n_quit}.pdf"'
    return response
