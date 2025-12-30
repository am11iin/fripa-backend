# Fripa Backend API

## Déploiement

### Option 1: Railway (Recommandé pour débutants)
1. Créer un compte sur [Railway](https://railway.app)
2. Connecter votre repository GitHub
3. Railway détectera automatiquement le Dockerfile
4. Déployer en 1 clic

### Option 2: Vercel (Excellent pour les APIs)
1. Installer Vercel CLI: `npm i -g vercel`
2. Se connecter: `vercel login`
3. Déployer: `vercel --prod`

### Option 3: Heroku
1. Créer un compte sur [Heroku](https://heroku.com)
2. Installer Heroku CLI
3. Créer l'app: `heroku create votre-app`
4. Déployer: `git push heroku main`

### Option 4: Docker (Auto-hébergement)
```bash
# Build et run localement
docker-compose up --build

# Ou avec Docker directement
docker build -t fripa-backend .
docker run -p 8000:8000 fripa-backend
```

### Option 5: PythonAnywhere (Simple)
1. Créer un compte sur [PythonAnywhere](https://pythonanywhere.com)
2. Upload les fichiers
3. Installer requirements.txt
4. Configurer le web app avec Gunicorn

## Configuration des variables d'environnement

Dans votre plateforme d'hébergement, configurez:
- `ADMIN_PASSWORD=fripaAdmin123`
- `DATABASE_URL=sqlite:///./fripa.db`
- `ENVIRONMENT=production`

## Endpoints disponibles

- `GET /` - API status
- `GET /products` - Lister tous les produits
- `POST /products` - Ajouter un produit (admin)
- `PUT /products/{id}` - Modifier un produit (admin)
- `DELETE /products/{id}` - Supprimer un produit (admin)
- `POST /checkout` - Passer une commande
- `GET /admin/orders` - Voir les commandes (admin)

## Test après déploiement

Une fois déployé, testez avec:
```bash
curl https://votre-domaine.railway.app/
```
