FROM node:22-bookworm-slim

WORKDIR /app

COPY package.json package-lock.json ./
# Installing the browser through the locked Playwright version keeps the two in sync.
RUN npm ci \
	&& npx playwright install --with-deps chromium \
	&& rm -rf /var/lib/apt/lists/*

COPY playwright.config.js ./
COPY tests ./tests

CMD ["npx", "playwright", "test"]
