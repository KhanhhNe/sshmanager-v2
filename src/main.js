import Vue from 'vue'
import App from './App.vue'
import moment from "moment";

moment.locale('vi')

Vue.config.productionTip = false

new Vue({
  render: h => h(App),
}).$mount('#app')
