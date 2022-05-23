import {createApp, h} from 'vue'
import App from './App.vue'
import './index.css'
import moment from 'moment'
import './assets/tailwind.css'

moment.locale('vi')

const app = createApp({
  render: () => h(App)
})
app.mount('#app')
