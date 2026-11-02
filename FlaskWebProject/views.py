"""Routes and views for the Article CMS."""
from urllib.parse import quote, urlparse
import uuid

import msal
from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from config import Config
from FlaskWebProject import app
from FlaskWebProject.forms import LoginForm, PostForm
from FlaskWebProject.models import Post, User

imageSourceUrl = (
    f"https://{app.config['BLOB_ACCOUNT']}.blob.core.windows.net/"
    f"{app.config['BLOB_CONTAINER']}/"
)


@app.route("/")
@app.route("/home")
@login_required
def home():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template("index.html", title="Home Page", posts=posts)


@app.route("/new_post", methods=["GET", "POST"])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post_record = Post()
        post_record.save_changes(form, form.image_path.data, current_user.id, new=True)
        app.logger.info("Article created by user=%s", current_user.username)
        return redirect(url_for("home"))
    return render_template(
        "post.html", title="Create Post", imageSource=imageSourceUrl, form=form
    )


@app.route("/post/<int:id>", methods=["GET", "POST"])
@login_required
def post(id):
    post_record = Post.query.get_or_404(id)
    form = PostForm(obj=post_record)
    if form.validate_on_submit():
        post_record.save_changes(form, form.image_path.data, current_user.id)
        app.logger.info("Article updated: id=%s user=%s", id, current_user.username)
        return redirect(url_for("home"))
    return render_template(
        "post.html", title="Edit Post", imageSource=imageSourceUrl, form=form
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(form.password.data):
            app.logger.warning("Invalid login attempt for username=%s", username)
            flash("Invalid username or password", "danger")
            return redirect(url_for("login"))

        login_user(user, remember=form.remember_me.data)
        app.logger.info("%s logged in successfully", user.username)
        next_page = request.args.get("next")
        if not next_page or urlparse(next_page).netloc:
            next_page = url_for("home")
        return redirect(next_page)

    session["state"] = str(uuid.uuid4())
    auth_url = None
    if Config.CLIENT_ID and Config.CLIENT_SECRET:
        auth_url = _build_auth_url(scopes=Config.SCOPE, state=session["state"])
    else:
        app.logger.warning("Microsoft sign-in is not configured")
    return render_template("login.html", title="Sign In", form=form, auth_url=auth_url)


@app.route(Config.REDIRECT_PATH)
def authorized():
    if request.args.get("state") != session.get("state"):
        app.logger.warning("Microsoft login rejected because OAuth state did not match")
        flash("The Microsoft sign-in response could not be verified.", "danger")
        return redirect(url_for("login"))

    if "error" in request.args:
        app.logger.warning(
            "Microsoft login failed: %s",
            request.args.get("error_description", request.args.get("error")),
        )
        return render_template("auth_error.html", result=request.args)

    code = request.args.get("code")
    if code:
        cache = _load_cache()
        result = _build_msal_app(cache=cache).acquire_token_by_authorization_code(
            code,
            scopes=Config.SCOPE,
            redirect_uri=url_for("authorized", _external=True, _scheme="https"),
        )
        if "error" in result:
            app.logger.warning(
                "Microsoft login failed: %s",
                result.get("error_description", result.get("error")),
            )
            return render_template("auth_error.html", result=result)

        claims = result.get("id_token_claims", {})
        session["user"] = claims
        user = User.query.filter_by(username="admin").first()
        if user is None:
            app.logger.error("Microsoft login succeeded but local admin user was not found")
            flash("The local administrator account is not configured.", "danger")
            return redirect(url_for("login"))

        login_user(user)
        _save_cache(cache)
        app.logger.info(
            "Microsoft login successful for account=%s",
            claims.get("preferred_username") or claims.get("name") or "unknown",
        )

    return redirect(url_for("home"))


@app.route("/logout")
def logout():
    username = current_user.username if current_user.is_authenticated else "anonymous"
    used_microsoft_login = bool(session.get("user"))
    logout_user()
    app.logger.info("User logged out: %s", username)

    if used_microsoft_login:
        session.clear()
        post_logout = url_for("login", _external=True, _scheme="https")
        return redirect(
            f"{Config.AUTHORITY}/oauth2/v2.0/logout"
            f"?post_logout_redirect_uri={quote(post_logout, safe='')}"
        )

    session.clear()
    return redirect(url_for("login"))


def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache


def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()


def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        Config.CLIENT_ID,
        authority=authority or Config.AUTHORITY,
        client_credential=Config.CLIENT_SECRET,
        token_cache=cache,
    )


def _build_auth_url(authority=None, scopes=None, state=None):
    return _build_msal_app(authority=authority).get_authorization_request_url(
        scopes or Config.SCOPE,
        state=state,
        redirect_uri=url_for("authorized", _external=True, _scheme="https"),
    )
