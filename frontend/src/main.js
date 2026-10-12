import { createApp } from 'vue';
import { createPinia } from 'pinia';
import PrimeVue from 'primevue/config';
import Aura from '@primeuix/themes/aura';
import 'primeicons/primeicons.css';
import './style.css';
import App from './App.vue';
createApp(App).use(createPinia()).use(PrimeVue,{theme:{preset:Aura,options:{darkModeSelector:'.dark-theme'}}}).mount('#app');
