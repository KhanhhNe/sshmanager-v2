import {createApp, h} from 'vue'
import App from './App.vue'
import moment from "moment";
import {createPinia} from "pinia";

moment.locale('vi')

const app = createApp({
    render: () => h(App),
})
app.use(createPinia())
app.mount('#app')
