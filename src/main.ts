import { createApp } from "vue";
import { createPinia } from "pinia";
import { createI18n } from "vue-i18n";
import "./style.css";
import App from "./App.vue";

import es from "./locales/es.json";
import en from "./locales/en.json";

const i18n = createI18n({
  legacy: false,
  locale: "en",
  fallbackLocale: "es",
  messages: { es, en },
});

const pinia = createPinia();
const app = createApp(App);

app.use(pinia);
app.use(i18n);
app.mount("#app");
