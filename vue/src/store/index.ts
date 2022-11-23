import { createStore } from "vuex";
import { wbsStore } from "wbs/vue/wbsStore";

export default createStore({
    modules: { wbs: wbsStore },
});
