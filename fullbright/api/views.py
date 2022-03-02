

from email import message
import json
from django.db.models.expressions import Case, When
from rest_framework import pagination
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from itertools import chain
from django.db.models.aggregates import Count, Sum
from django.db.models.base import Model
from django.db.models.query import QuerySet
from django.db.models import Q
from rest_framework.serializers import Serializer
from .models import *
from .serializers import *
from django.http import Http404, response
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from .serializers import ArticleSerializer, EditionSerializer, JournalSerializer
from .models import Journal, Edition, Article
from rest_framework import filters
from datetime import date, datetime
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.permissions import IsAdminUser, IsAuthenticated
import jwt
from fullbright.settings import SIMPLE_JWT
from users.serializers import *
from rest_framework import permissions
from datetime import datetime
import pandas as pd


class JournalPermissions(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in ['POST', 'GET'] and request.user.groups.filter(name="Voir journal").exists():
            return True
        if request.method in ['POST', 'GET', 'PUT', 'PATCH', 'DELETE'] and request.user.groups.filter(name="Modifier journal").exists():
            return True
        return False


class AfficheurPermissions(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in ['POST', 'GET'] and request.user.groups.filter(name="Voir afficheur").exists():
            return True
        if request.method in ['POST', 'GET', 'PUT', 'PATCH', 'DELETE'] and request.user.groups.filter(name="Modifier afficheur").exists():
            return True
        return False


class AnnonceurPermissions(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in ['POST', 'GET'] and request.user.groups.filter(name="Voir annonceur").exists():
            return True
        if request.method in ['POST', 'GET', 'PUT', 'PATCH', 'DELETE'] and request.user.groups.filter(name="Modifier annonceur").exists():
            return True
        return False


class ChainePermissions(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in ['POST', 'GET'] and request.user.groups.filter(name="Voir chaine").exists():
            return True
        if request.method in ['POST', 'GET', 'PUT', 'PATCH', 'DELETE'] and request.user.groups.filter(name="Modifier chaine").exists():
            return True
        return False


class MyPagination(pagination.PageNumberPagination):
    page_size = 6
    page_size_query_param = 'page_size'
    max_page_size = 10000

    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'results': data
        })


class JournalViewTest(generics.ListCreateAPIView):
    queryset = Journal.objects.all()
    serializer_class = JournalSerializer


class JournalView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated & JournalPermissions]
    pagination_class = MyPagination
    queryset = Journal.objects.all()
    serializer_class = JournalSerializer


class UpdateJournalView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated & JournalPermissions]
    queryset = Journal.objects.all()
    serializer_class = JournalSerializer
    lookup_fields = ['pk']


class Journalsearch(generics.ListAPIView):
    # queryset = Journal.objects.all()
    permission_classes = [IsAuthenticated & JournalPermissions]
    serializer_class = JournalSerializer

    def get_queryset(self):
        nom = self.request.query_params.get('nomJournal')
        queryset = Journal.objects.filter(nomJournal=nom)
        return queryset


# ---------------------------------------------------------------------------------------------


class EditionView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated & JournalPermissions]
    serializer_class = EditionSerializer

    def get_queryset(self):
        j = self.request.query_params.get('journal')
        queryset = Edition.objects.filter(journal=j).order_by('-date')
        return queryset
# ---------------------------------------------------------------------------------------------


class EditionSearch(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated & JournalPermissions]
    serializer_class = EditionSerializer
    pagination_class = MyPagination

    def get_queryset(self):
        journal = self.request.query_params.get('journal')
        qset = Edition.objects.filter(journal=journal).order_by('-date')
        start = self.request.query_params.get('start')
        end = self.request.query_params.get('end')
        querySet = [edition for edition in qset
                    if edition.date >= datetime.strptime(start, '%Y-%m-%d').date()
                    and edition.date <= datetime.strptime(end, '%Y-%m-%d').date()]
        return querySet
# ---------------------------------------------------------------------------------------------


class UpdateEditioneView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated & JournalPermissions]
    queryset = Edition.objects.all()
    serializer_class = EditionSerializer


class Editioncount(generics.ListAPIView):
    permission_classes = [IsAuthenticated & JournalPermissions]
    serializer_class = EditionSerializer

    def get_queryset(self):
        nom = self.request.query_params.get('journal')
        queryset = Edition.objects.filter(journal=nom)
        return queryset

# ---------------------------------------------------------------------------------------------


class ArticleView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated & JournalPermissions]
    serializer_class = ArticleSerializer

    def get_queryset(self):
        edition = self.request.query_params.get('edition')
        queryset = Article.objects.filter(
            edition=edition, confirmed=True).order_by('-date_creation')
        return queryset


class ArticleConfirmed(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ArticleSerializer
    pagination_class = MyPagination

    def get_queryset(self):
        queryset = Article.objects.filter(
            confirmed=False).order_by('-date_creation')
        return queryset


class ArticleConfirmedCount(APIView):
    permission_classes = [IsAuthenticated & JournalPermissions & IsAdminUser]

    def get(self, request, format=None):
        count = Article.objects.filter(
            confirmed=False).count()

        return Response(count)


class UpdateArticleView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated & JournalPermissions]
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    lookup_fields = ['pk']


class Articlesearch(generics.ListAPIView):
    permission_classes = [IsAuthenticated & JournalPermissions]
    serializer_class = ArticleSerializer

    def get(self, request, format=None):
        jr = self.request.query_params.get('jr')
        edts = Edition.objects.filter(journal=jr).annotate(
            num_article=Count('article', filter=Q(article__confirmed=True))).aggregate(Sum("num_article"))

        if not edts['num_article__sum']:
            edts['num_article__sum'] = 0

        return Response({"nbjr": edts['num_article__sum']})


# ---------------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------------

# API pour la table Afficheur :
# AfficheurView : pour  la recuperation de la table entiere.
# AfficheurDetail : pour get,update,delete pour les instances
class AfficheurView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated & AfficheurPermissions]
    queryset = Afficheur.objects.all()
    serializer_class = AfficheurSerializer
# ---------------------------------------------------------------------------------------------


class AfficheurDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated & AfficheurPermissions]
    queryset = Afficheur.objects.all()
    serializer_class = AfficheurSerializer
    lookup_fields = ['pk']


class Afficheursearch(generics.ListAPIView):
    serializer_class = AfficheurSerializer

    def get_queryset(self):
        nom = self.request.query_params.get('nom_afficheur')
        if nom == None:
            return Afficheur.objects.all()
        queryset = Afficheur.objects.filter(nom_afficheur=nom)
        return queryset


# ---------------------------------------------------------------------------------------------
class getAfficheurInfo(generics.ListAPIView):
    permission_classes = [IsAuthenticated & AfficheurPermissions]
    pagination_class = MyPagination
    serializer_class = AfficheurSerializer
    queryset = Afficheur.objects.all()


# ---------------------------------------------------------------------------------------------

# API pour la table Panneau :
# PanneauView : pour  la recuperation de la table entiere.
# PanneauDetail : pour get,update,delete pour les instances

class PanneauView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated & AfficheurPermissions]
    serializer_class = PanneauSerializer
    pagination_class = MyPagination

    def get_queryset(self):
        nom = self.request.query_params.get('afficheur')
        queryset = Panneau.objects.filter(afficheur=nom)
        return queryset


class PanneauDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated & AfficheurPermissions]
    queryset = Panneau.objects.all()
    serializer_class = PanneauSerializer
    lookup_fields = ['pk']


class PanneauFilter(generics.ListAPIView):
    permission_classes = [IsAuthenticated & AfficheurPermissions]
    serializer_class = PanneauSerializer

    def get_queryset(self):
        afficheur = self.request.query_params.get('afficheur')
        queryset = Panneau.objects.filter(
            afficheur=afficheur)
        return queryset
# ---------------------------------------------------------------------------------------------

# API pour la table Pub :
# PubView : pour  la recuperation de la table entiere.
# PubView : pour get,update,delete pour les instances


class PubView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated & AfficheurPermissions]
    serializer_class = PubSerializer
    pagination_class = MyPagination

    def get_queryset(self):
        nom = self.request.query_params.get('panneau')
        queryset = Pub.objects.filter(panneau=nom, confirmed=True)
        return queryset


class PubCount(APIView):
    permission_classes = [IsAuthenticated & AfficheurPermissions]

    def get(self, request, format=None):
        nom = self.request.query_params.get('panneau')
        count = Pub.objects.filter(panneau=nom).count()
        return Response(count)


class PubDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated & AfficheurPermissions]
    queryset = Pub.objects.all()
    serializer_class = PubSerializer
    lookup_fields = ['pk']


class PubConfirmation(generics.ListCreateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = PubSerializer
    pagination_class = MyPagination

    def get_queryset(self):
        queryset = Pub.objects.filter(confirmed=False)
        return queryset


class PubConfirmedCount(APIView):
    permission_classes = [IsAuthenticated & AfficheurPermissions]

    def get(self, request, format=None):
        count = Pub.objects.filter(
            confirmed=False).count()

        return Response(count)


class PubFilter(generics.ListAPIView):
    permission_classes = [IsAuthenticated & AfficheurPermissions]
    serializer_class = PubSerializer
    pagination_class = MyPagination

    def get_queryset(self):
        langue = self.request.query_params.get('langue')
        annonceur = self.request.query_params.get('annonceur')
        marque = self.request.query_params.get('marque')
        produit = self.request.query_params.get('produit')
        panneau = self.request.query_params.get('panneau')
        start = self.request.query_params.get('start')
        end = self.request.query_params.get('end')

        if(annonceur and not marque and not produit):
            queryset = Pub.objects.filter(
                annonceur=annonceur,
                langue__icontains=langue,
                panneau=panneau,
                confirmed=True
            )

        elif(annonceur and marque and not produit):
            queryset = Pub.objects.filter(
                annonceur=annonceur,
                marque=marque,
                langue__icontains=langue,
                panneau=panneau, confirmed=True
            )
        elif(annonceur and marque and produit):
            queryset = Pub.objects.filter(
                annonceur=annonceur,
                marque=marque,
                produit=produit,
                langue__icontains=langue,
                panneau=panneau, confirmed=True
            )
        elif(not annonceur and not marque and not produit):
            queryset = Pub.objects.filter(
                langue__icontains=langue,
                panneau=panneau, confirmed=True)

        queryset = [pub for pub in queryset
                    if pub.date_creation >= datetime.strptime(start, '%Y-%m-%d').date()
                    and pub.date_creation <= datetime.strptime(end, '%Y-%m-%d').date()]

        return queryset

# --------------------------------------------------------------------------------------


class AnnonceurView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated & AnnonceurPermissions]
    queryset = Annonceur.objects.all()
    pagination_class = MyPagination
    serializer_class = AnnonceurSerializer


class GetAnnonceurs(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Annonceur.objects.all()
    serializer_class = AnnonceurSerializer


class AnnonceurDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated & AnnonceurPermissions]
    queryset = Annonceur.objects.all()
    serializer_class = AnnonceurSerializer
    lookup_fields = ['pk']


class AnnonceurExiste(APIView):
    permission_classes = [IsAuthenticated & AnnonceurPermissions]

    def get(self, request, format=None):
        nom = self.request.query_params.get('annonceur')
        bool = Annonceur.objects.filter(Nom=nom).exists()
        return Response(bool)


class Annonceursearch(generics.ListAPIView):
    serializer_class = AnnonceurSerializer

    def get_queryset(self):
        nom = self.request.query_params.get('Nom')
        if nom == None:
            return Annonceur.objects.all()
        queryset = Annonceur.objects.filter(Nom=nom)
        return queryset


class MarqueView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated & AnnonceurPermissions]
    serializer_class = MarqueSerializer
    pagination_class = MyPagination

    def get_queryset(self):
        nom = self.request.query_params.get('annonceur')
        queryset = Marque.objects.filter(NomAnnonceur=nom)
        return queryset


class MarqueExiste(APIView):
    permission_classes = [IsAuthenticated & AnnonceurPermissions]

    def get(self, request, format=None):
        nom = self.request.query_params.get('marque')
        bool = Marque.objects.filter(Nom=nom).exists()
        return Response(bool)


class MarqueDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated & AnnonceurPermissions]
    queryset = Marque.objects.all()
    serializer_class = MarqueSerializer
    lookup_fields = ['pk']


class MarqueSearch(generics.ListAPIView):
    serializer_class = MarqueSerializer

    def get_queryset(self):
        nom = self.request.query_params.get('Nom')
        nomAnn = self.request.query_params.get('annonceur')
        if nom == None:
            return Marque.objects.filter(NomAnnonceur=nomAnn)
        queryset = Marque.objects.filter(Nom=nom)
        return queryset


class MarqueSearchContract(generics.ListCreateAPIView):
    serializer_class = MarqueSerializer
    queryset = Marque.objects.all()

    def post(self):
        nomAnn = self.request.query_params.get('NomAnnonceur')
        queryset = Marque.objects.filter(NomAnnonceur__in=nomAnn)
        return queryset


class ProduitView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated & AnnonceurPermissions]
    serializer_class = ProduitSerializer
    pagination_class = MyPagination

    def get_queryset(self):
        nom = self.request.query_params.get('marque')
        queryset = Produit.objects.filter(NomMarque=nom)
        return queryset


class ProduitDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated & AnnonceurPermissions]
    queryset = Produit.objects.all()
    serializer_class = ProduitSerializer
    lookup_fields = ['pk']


class ProduitExiste(APIView):
    permission_classes = [IsAuthenticated & AnnonceurPermissions]

    def get(self, request, format=None):
        nom = self.request.query_params.get('produit')
        bool = Produit.objects.filter(Nom=nom).exists()
        return Response(bool)


class ProduitSearch(generics.ListAPIView):
    serializer_class = ProduitSerializer

    def get_queryset(self):
        nom = self.request.query_params.get('Nom')
        nomM = self.request.query_params.get('marque')
        if nom == None:
            return Produit.objects.filter(NomMarque=nomM)
        queryset = Produit.objects.filter(Nom=nom)
        return queryset
# --------------------------------------------------------------------------------------------------


class AbonnementView(generics.ListCreateAPIView):
    queryset = Abonnement.objects.all()
    serializer_class = AbonnementSerializer


class AbonnementDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Abonnement.objects.all()
    serializer_class = AbonnementSerializer
    lookup_fields = ['pk']


class Abonnementsearch(generics.ListAPIView):
    serializer_class = AbonnementSerializer

    def get_queryset(self):
        abn = self.request.query_params.get('client')
        queryset = Abonnement.objects.filter(client=abn)
        return queryset


class WilayaView(generics.ListCreateAPIView):
    queryset = Wilaya.objects.all()
    serializer_class = WilayaSerializer


class ApcView(generics.ListCreateAPIView):
    queryset = Apc.objects.all()
    serializer_class = ApcSerializer


class CommunView(generics.ListCreateAPIView):
    queryset = Commune.objects.all()
    serializer_class = CommuneSerializer


# --------------------------------------------------------------------------------------------------


class ContractView(generics.ListAPIView):
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer


class ContractPost(generics.CreateAPIView):
    queryset = Contract.objects.all()

    def post(self, request):
        ok = {
            "abonnement": request.query_params.get('abonnement'),
            "produits": list(map(int, request.query_params.getlist('produit[]'))),
            "annonceurs": list(map(int, request.query_params.getlist('annonceur[]'))),
            "marques": list(map(int, request.query_params.getlist('marque[]'))),
            "date_debut": request.query_params.get('date_debut'),
            "date_fin": request.query_params.get('date_fin')
        }
        serializer = ContractSerializerPost(data=ok)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContractDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    lookup_fields = ['pk']


class Contractsearch(generics.ListAPIView):
    serializer_class = ContractSerializer

    def get_queryset(self):
        ctr = self.request.query_params.get('abonnement')
        queryset = Contract.objects.filter(abonnement=ctr)
        return queryset

# --------------------------------------------------------------------------------------------------


class MarqueFilter(generics.ListAPIView):
    permission_classes = [IsAuthenticated & AnnonceurPermissions]
    serializer_class = MarqueSerializer

    def get_queryset(self):
        NomAnnonceur = self.request.query_params.get('NomAnnonceur')
        queryset = Marque.objects.filter(NomAnnonceur=NomAnnonceur)
        return queryset


class MarqueFilterForContract(generics.ListAPIView):
    permission_classes = [IsAuthenticated & AnnonceurPermissions]
    serializer_class = MarqueSerializer

    def get_queryset(self):
        NomAnnonceur = self.request.query_params.getlist('NomAnnonceur[]')
        queryset = Marque.objects.filter(NomAnnonceur__in=NomAnnonceur)
        return queryset


class ProduitFilter(generics.ListAPIView):
    permission_classes = [IsAuthenticated & AnnonceurPermissions]
    serializer_class = ProduitSerializer

    def get_queryset(self):
        NomMarque = self.request.query_params.get('NomMarque')
        queryset = Produit.objects.filter(NomMarque=NomMarque)
        return queryset


class ProduitFilterForContract(generics.ListAPIView):
    permission_classes = [IsAuthenticated & AnnonceurPermissions]
    serializer_class = ProduitSerializer

    def get_queryset(self):
        NomMarque = self.request.query_params.getlist('NomMarque[]')
        queryset = Produit.objects.filter(NomMarque__in=NomMarque)
        return queryset


class SearchFilter(generics.ListAPIView):
    # permission_classes = [IsAuthenticated & AnnonceurPermissions]
    serializer_class = ArticleSerializer
    pagination_class = MyPagination

    def get_queryset(self):
        accroche = self.request.query_params.get('accroche')
        langue = self.request.query_params.get('langue')
        annonceur = self.request.query_params.get('annonceur')
        marque = self.request.query_params.get('marque')
        produit = self.request.query_params.get('produit')
        edition = self.request.query_params.get('edition')
        start = self.request.query_params.get('start')
        end = self.request.query_params.get('end')

        if(annonceur and not marque and not produit):
            queryset = Article.objects.filter(
                accroche__icontains=accroche,
                annonceur=annonceur,
                language__icontains=langue,
                edition=edition,
                confirmed=True
            )

        elif(annonceur and marque and not produit):
            queryset = Article.objects.filter(
                accroche__icontains=accroche,
                annonceur=annonceur,
                marque=marque,
                language__icontains=langue,
                edition=edition,
                confirmed=True
            )
        elif(annonceur and marque and produit):
            queryset = Article.objects.filter(
                accroche__icontains=accroche,
                annonceur=annonceur,
                marque=marque,
                produit=produit,
                language__icontains=langue,
                edition=edition,
                confirmed=True
            )
        elif(not annonceur and not marque and not produit):
            queryset = Article.objects.filter(
                accroche__icontains=accroche,
                language__icontains=langue,
                edition=edition,
                confirmed=True)

        queryset = [article for article in queryset
                    if article.date_creation >= datetime.strptime(start, '%Y-%m-%d').date()
                    and article.date_creation <= datetime.strptime(end, '%Y-%m-%d').date()]

        return queryset


class WilayaView(generics.ListCreateAPIView):
    queryset = Wilaya.objects.all()
    serializer_class = WilayaSerializer

# --------------------------------------------------------------------------------------------------


class ApcView(generics.ListCreateAPIView):
    queryset = Apc.objects.all()
    serializer_class = ApcSerializer


class Apcsearch(generics.ListAPIView):
    serializer_class = ApcSerializer

    def get_queryset(self):
        nom = self.request.query_params.get('commune')
        queryset = Apc.objects.filter(commune=nom)
        return queryset
# --------------------------------------------------------------------------------------------------


class CommuneView(generics.ListCreateAPIView):
    queryset = Commune.objects.all()
    serializer_class = CommuneSerializer


class Communesearch(generics.ListAPIView):
    serializer_class = CommuneSerializer

    def get_queryset(self):
        nom = self.request.query_params.get('wilaya')
        queryset = Commune.objects.filter(Wilaya=nom)
        return queryset


class getProduitMarqueAnnonceur(APIView):
    permission_classes = [IsAuthenticated & AnnonceurPermissions]

    def get(self, request, format=None):
        produitId = self.request.query_params.get('produit')
        produit = Produit.objects.filter(id=produitId)
        marque = Marque.objects.filter(id=produit[0].NomMarque.id)
        annonceur = Annonceur.objects.filter(id=marque[0].NomAnnonceur.id)

        data = {
            "produit": produit[0].Nom,
            "marque": marque[0].Nom,
            "annonceur": annonceur[0].Nom
        }

        return Response(data)





class ArticleClientView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ArticleClientSerializer
    pagination_class = MyPagination

    def get_queryset(self):
        accroche = self.request.query_params.get('accroche')
        langue = self.request.query_params.get('langue')
        annonceur1 = self.request.query_params.get('annonceur')
        marque1 = self.request.query_params.get('marque')
        produit1 = self.request.query_params.get('produit')
        journal = self.request.query_params.get('journal')
        start = self.request.query_params.get('start')
        end = self.request.query_params.get('end')

        if self.request.user.is_client == True:
            qs = Article.objects.none()
            for abonnement in self.request.user.abonnement_set.all():
                if timezone.now().date() <= abonnement.date_fin and abonnement.service == 'J':
                    for contract in abonnement.contract_set.all():
                        for annonceur in contract.annonceurs.all():
                            if contract.marques.filter(NomAnnonceur=annonceur).exists():
                                for marque in contract.marques.filter(NomAnnonceur=annonceur):
                                    if contract.produits.filter(NomMarque=marque).exists():
                                        for produit in contract.produits.filter(NomMarque=marque):
                                            qs = qs | produit.article_set.all()
                                    else:
                                        qs = qs | marque.article_set.all()
                            else:
                                qs = qs | annonceur.article_set.all()

            queryset = qs.filter(
                accroche__icontains=accroche,
                language__icontains=langue,
                confirmed=True
            )
            if(annonceur1):
                queryset = queryset.filter(
                    annonceur=annonceur1
                )
            if(marque1):
                queryset = queryset.filter(
                    marque=marque1
                )
            if(produit1):
                queryset = queryset.filter(
                    produit=produit1
                )

            articles = Article.objects.none()
            for abonnement in self.request.user.abonnement_set.all():
                if timezone.now().date() <= abonnement.date_fin and abonnement.service == 'J':
                    for contract in abonnement.contract_set.all():
                        articles = articles | queryset.filter(date_creation__range=(datetime.strptime(
                            start, '%Y-%m-%d'), datetime.strptime(end, '%Y-%m-%d'))).filter(
                            date_creation__range=(contract.date_debut, contract.date_fin))

            return articles


class PubClientView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PubClientSerializer
    pagination_class = MyPagination

    def get_queryset(self):

        langue = self.request.query_params.get('langue')
        annonceur1 = self.request.query_params.get('annonceur')
        marque1 = self.request.query_params.get('marque')
        produit1 = self.request.query_params.get('produit')
        start = self.request.query_params.get('start')
        end = self.request.query_params.get('end')

        if self.request.user.is_client == True:
            qs = Pub.objects.none()
            for abonnement in self.request.user.abonnement_set.all():
                if timezone.now().date() <= abonnement.date_fin and abonnement.service == 'P':
                    for contract in abonnement.contract_set.all():
                        for annonceur in contract.annonceurs.all():
                            if contract.marques.filter(NomAnnonceur=annonceur).exists():
                                for marque in contract.marques.filter(NomAnnonceur=annonceur):
                                    if contract.produits.filter(NomMarque=marque).exists():
                                        for produit in contract.produits.filter(NomMarque=marque):
                                            qs = qs | produit.pub_set.all()
                                    else:
                                        qs = qs | marque.pub_set.all()
                            else:
                                qs = qs | annonceur.pub_set.all()
            queryset = qs.filter(
                langue__icontains=langue,
                confirmed=True
            )
            if(annonceur1):
                queryset = queryset.filter(
                    annonceur=annonceur1
                )
            if(marque1):
                queryset = queryset.filter(
                    marque=marque1
                )
            if(produit1):
                queryset = queryset.filter(
                    produit=produit1
                )

            print("######################################################")
            pubs = Pub.objects.none()
            for abonnement in self.request.user.abonnement_set.all():
                if timezone.now().date() <= abonnement.date_fin and abonnement.service == 'P':
                    for contract in abonnement.contract_set.all():
                        pubs = pubs | queryset.filter(date_creation__range=(datetime.strptime(
                            start, '%Y-%m-%d'), datetime.strptime(end, '%Y-%m-%d'))).filter(
                            date_creation__range=(contract.date_debut, contract.date_fin))

            return pubs


class ClientAbonnement(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AbonnementSerializer

    def get_queryset(self):
        if self.request.user.is_client == True:
            return self.request.user.abonnement_set.all()


class ContractViewClient(generics.ListCreateAPIView):
    serializer_class = ContractSerializer

    def get_queryset(self):
        return Contract.objects.filter(
            abonnement=self.request.query_params.get('abonnoment'))




class VideoConfirmedCount(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, format=None):
        count = Publicite.objects.filter(
            confirmed=False).count()
        return Response(count)


class VideoConfirmation(generics.ListCreateAPIView):
    permission_classes = [IsAdminUser]
    queryset = Publicite.objects.all()
    serializer_class = PubliciteSerializer
    pagination_class = MyPagination

    def get_queryset(self):
        return Publicite.objects.filter(confirmed=False)


class ChaineView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated & ChainePermissions]
    queryset = Chaine.objects.all().order_by("nom")
    serializer_class = ChaineSerializer
    pagination_class = MyPagination


class ChaineAllView(generics.ListAPIView):
    queryset = Chaine.objects.all().order_by("nom")
    serializer_class = ChaineSerializer


class ChaineDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated & ChainePermissions]
    queryset = Chaine.objects.all()
    serializer_class = ChaineSerializer
    lookup_fields = ['pk']


class Chainesearch(generics.ListAPIView):
    permission_classes = [IsAuthenticated & ChainePermissions]
    serializer_class = ChaineSerializer

    def get_queryset(self):
        nom = self.request.query_params.get('nom')
        if nom == None:
            return Chaine.objects.all()
        queryset = Chaine.objects.filter(nom=nom)

        return queryset


class ArticleLinkClient(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Article.objects.all()
    serializer_class = ArticleClientSerializer

    def get_queryset(self):
        id = self.request.query_params.get('id')
        if self.request.user.is_client == True:
            qs = Article.objects.none()
            for abonnement in self.request.user.abonnement_set.all():
                if timezone.now().date() <= abonnement.date_fin and abonnement.service == "J":
                    for contract in abonnement.contract_set.all():
                        for annonceur in contract.annonceurs.all():
                            if contract.marques.filter(NomAnnonceur=annonceur).exists():
                                for marque in contract.marques.filter(NomAnnonceur=annonceur):
                                    if contract.produits.filter(NomMarque=marque).exists():
                                        for produit in contract.produits.filter(NomMarque=marque):
                                            qs = qs | produit.article_set.all()
                                    else:
                                        qs = qs | marque.article_set.all()
                            else:
                                qs = qs | annonceur.article_set.all()
            return qs.filter(id=id)


class PubLinkClient(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Pub.objects.all()
    serializer_class = PubClientSerializer

    def get_queryset(self):
        id = self.request.query_params.get('id')
        if self.request.user.is_client == True:
            qs = Pub.objects.none()
            for abonnement in self.request.user.abonnement_set.all():
                if timezone.now().date() <= abonnement.date_fin and abonnement.service == "P":
                    for contract in abonnement.contract_set.all():
                        for annonceur in contract.annonceurs.all():
                            if contract.marques.filter(NomAnnonceur=annonceur).exists():
                                for marque in contract.marques.filter(NomAnnonceur=annonceur):
                                    if contract.produits.filter(NomMarque=marque).exists():
                                        for produit in contract.produits.filter(NomMarque=marque):
                                            qs = qs | produit.pub_set.all()
                                    else:
                                        qs = qs | marque.pub_set.all()
                            else:
                                qs = qs | annonceur.pub_set.all()
            return qs.filter(id=id)


class send_email(APIView):
    #permission_classes = [IsAdminUser]

    def post(self, request, format=None):

        print("##########################################")
        clients = User.objects.filter(is_client=True, is_active=True)
        print("##########################################")

        for client in clients:

            qs = Article.objects.none()
            for abonnement in client.abonnement_set.all():
                if timezone.now().date() <= abonnement.date_fin and abonnement.service == 'J':
                    for contract in abonnement.contract_set.all():
                        for annonceur in contract.annonceurs.all():
                            if contract.marques.filter(NomAnnonceur=annonceur).exists():
                                for marque in contract.marques.filter(NomAnnonceur=annonceur):
                                    if contract.produits.filter(NomMarque=marque).exists():
                                        for produit in contract.produits.filter(NomMarque=marque):
                                            qs = qs | produit.article_set.filter(
                                                date_creation=date.today())
                                    else:
                                        qs = qs | marque.article_set.filter(
                                            date_creation=date.today())
                            else:
                                qs = qs | annonceur.article_set.filter(
                                    date_creation=date.today())
        print(qs)
        print("##########################################")

        emailm = """
        <!DOCTYPE html>
<html>
	<table style="border-collapse: collapse;
	margin: 25px 0;
	font-size: 0.9em;
	min-width: 400px;
	border-radius: 5px 5px 0 0;
	overflow: hidden;
	box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);width: 100%;font-family: sans-serif;" >
		<thead style="background-color: #0070f3;
		color: #ffffff;
		text-align: left;
		font-weight: bold;">
			<tr style="background-color: #0070f3;
			color: #ffffff;
			text-align: left;
			font-weight: bold;">
				<th style="padding: 12px 15px;">Journal</th>
				<th style="padding: 12px 15px;">Accroche</th>
				<th style="padding: 12px 15px;">Date</th>
				<th style="padding: 12px 15px;">Annonceur</th>
				<th style="padding: 12px 15px;">Marque</th>
				<th style="padding: 12px 15px;">Produit</th>
				<th style="padding: 12px 15px;">Lien</th>
			</tr>
		</thead>
		<tbody style="border-bottom: 1px solid #dddddd;">
        
        
        """
        for article in qs:
            acc = ""
            if len(article.accroche) > 70:
                acc = article.accroche[:70]+" ..."
            else:
                acc = article.accroche
            emailm = emailm+"""
            <tr style="border-bottom: 1px solid #dddddd;color="black">
				<td style="padding: 12px 15px;">{}</td>
				<td>
					<div style="
					overflow: hidden;
					text-overflow: ellipsis;
					display: -webkit-box;
					-webkit-line-clamp: 1; /* number of lines to show */
							line-clamp: 1; 
					-webkit-box-orient: vertical;" >
                        {}
                    </div>
				</td>
				<td style="padding: 12px 15px;">{}</td>
				<td style="padding: 12px 15px;">{}</td>
				<td style="padding: 12px 15px;">{}</td>
				<td style="padding: 12px 15px;">{}</td>
				<td style="padding: 12px 15px;">
					<button style="
                    border: none;
                    padding: 0 10px;
					height: 35px;
					line-height: 25px;
					border-radius: 7px;
					background-color: #0070f3;
					color: white;
					
						">
						<a style="color: white;
						text-decoration: none;" href="{} ">
							lien
						</a>
					</button>
				</td>

			</tr>

            """.format(article.edition.journal.nomJournal, acc, article.date_creation, article.annonceur.Nom, article.marque.Nom if article.marque else '', article.produit.Nom if article.produit else '', "http://localhost:3001/article/link/"+str(article.id))

        emailm = emailm + """</tbody>
                                </table>
                            </html>"""

        email = EmailMessage('A new mail!', emailm, to=[
            'ghecharaf@gmail.com', 'fayssalbenaissa1513@gmail.com'])
        email.content_subtype = "html"
        email.send()
        return Response("ok")

# 'fayssalbenaissa1513@gmail.com'


class PubliciteView(generics.ListCreateAPIView):
    serializer_class = PubliciteSerializer
    queryset = Publicite.objects.all()
    permission_classes = [IsAuthenticated & ChainePermissions]


class PubliciteDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated & ChainePermissions]
    queryset = Publicite.objects.all()
    serializer_class = PubliciteSerializer
    lookup_fields = ['pk']


class ProgrammeView(generics.ListCreateAPIView):
    serializer_class = ProgrammeSerializer
    queryset = Programme.objects.all()
    permission_classes = [IsAuthenticated & ChainePermissions]

class UpdateProgrammeView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Programme.objects.all()
    serializer_class = ProgrammeSerializer
    permission_classes = [IsAuthenticated & ChainePermissions]

class JourDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated & ChainePermissions]
    queryset = Jour.objects.all()
    serializer_class = PubliciteSerializer
    lookup_fields = ['pk']


class JourView(generics.ListCreateAPIView):
    serializer_class = JourSerializer
    permission_classes = [IsAuthenticated & ChainePermissions]
    def get_queryset(self):
        id = self.request.query_params.get('id')
        queryset = Jour.objects.filter(chaine=id)
        return queryset

class JourViewClient(generics.ListAPIView):
    serializer_class = JourSerializer
    def get_queryset(self):
        id = self.request.query_params.get('id')
        queryset = Jour.objects.filter(chaine=id)
        return queryset


class ProgrammeEtPub(APIView):
    permission_classes = [IsAuthenticated & ChainePermissions]
    def get(self, request):
        id = self.request.query_params.get('id')
        publicite = Publicite.objects.filter(jour=id, confirmed=True)
        programme = Programme.objects.filter(jour=id)
        response = []
        i = 0
        for prog in programme:
            response.append({
                "id": i,
                "message": prog.message,
                "debut": prog.debut,
                "duree": prog.duree,
                "type": 1,
                "lien": prog.id,
                "ecran": ""
            })
            i += 1
        for pub in publicite:
            response.append({
                "id": i,
                "message": pub.message,
                "debut": pub.debut,
                "duree": pub.duree,
                "type": 2,
                "lien": pub.id,
                "ecran": pub.ecran
            })
            i += 1

        return Response(sorted(response, key=lambda d: d['debut']))


class ChaneiClientView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        jour = self.request.query_params.get('id')

        if self.request.user.is_client == True:

            qs = Publicite.objects.none()

            for abonnement in self.request.user.abonnement_set.all():
                if timezone.now().date() <= abonnement.date_fin and abonnement.service == "C":
                    for contract in abonnement.contract_set.all():
                        for annonceur in contract.annonceurs.all():
                            if contract.marques.filter(NomAnnonceur=annonceur).exists():
                                for marque in contract.marques.filter(NomAnnonceur=annonceur):
                                    if contract.produits.filter(NoMarque=marque).exists():
                                        for produit in contract.produits.filter(NomMarque=marque):
                                            qs = qs | produit.publicite_set.all()
                                    else:
                                        qs = qs | marque.publicite_set.all()
                            else:
                                qs = qs | annonceur.publicite_set.all()
            queryset = qs.filter(
                confirmed=True
            )

            videos = Publicite.objects.none()
            for abonnement in self.request.user.abonnement_set.all():
                if timezone.now().date() <= abonnement.date_fin and abonnement.service == 'C':
                    for contract in abonnement.contract_set.all():
                        if Jour.objects.filter(id=jour, date__range=(contract.date_debut, contract.date_fin)).exists():
                            videos = videos | queryset.filter(jour=jour)

            programme = Programme.objects.none()
            if len(videos):
                programme = Programme.objects.filter(jour=jour)

            response = []
            i = 0
            for prog in programme:
                response.append({
                    "id": i,
                    "message": prog.message,
                    "debut": prog.debut,
                    "duree": prog.duree,
                    "type": 1,
                    "lien": prog.id,
                    "ecran": ""
                })
                i += 1
            for pub in videos:
                response.append({
                    "id": i,
                    "message": pub.message,
                    "debut": pub.debut,
                    "duree": pub.duree,
                    "type": 2,
                    "lien": pub.id,
                    "ecran": pub.ecran
                })
                i += 1

            return Response(sorted(response, key=lambda d: d['debut']))
