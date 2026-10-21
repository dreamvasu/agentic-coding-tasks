FROM ruby:3.1-slim-bookworm

# build-essential + git: jekyll.gemspec lists files via `git ls-files`, which
# raises ENOENT (crashing bundle) if the git binary is absent; with git present
# in this non-repo checkout it simply returns empty, which is fine for a
# from-source run. The verifier is pure bash + the repo's own Ruby/Jekyll, so no
# Python or other verifier-only tooling is baked into the agent image.
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      git \
      ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY jekyll /app

# Install the repo's own bundle. The Gemfile pins jekyll-sass-converter "~> 2.2"
# (the libsass path), so no dart-sass / sass-embedded native build is needed.
RUN bundle install

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    JEKYLL_ENV=development \
    PYTHONUNBUFFERED=1
