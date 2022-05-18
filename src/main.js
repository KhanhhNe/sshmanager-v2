import {createApp, h} from 'vue'
import App from './App.vue'
import moment from "moment";

moment.locale('vi')

createApp({
    render: () => h(App),
}).mount('#app')
