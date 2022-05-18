import {createApp, h} from 'vue'
import App from './App.vue'
import moment from "moment";

moment.locale('vi')

const app = createApp({
    render: () => h(App),
})
app.mount('#app')
