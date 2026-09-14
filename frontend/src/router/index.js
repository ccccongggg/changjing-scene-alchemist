import { createRouter, createWebHistory } from 'vue-router'
import StartScreen from '../views/StartScreen.vue'
import SourceList from '../views/SourceList.vue'
import AdaptBench from '../views/AdaptBench.vue'
import MyLibrary from '../views/MyLibrary.vue'
import StarMap from '../views/StarMap.vue'
import StudentStepsStarmap from '../views/StudentStepsStarmap.vue'

const routes = [
  { path: '/', name: 'start', component: StartScreen },
  { path: '/bench', name: 'bench', component: SourceList },
  { path: '/starmap', name: 'starmap', component: StarMap },
  { path: '/steps/:sceneId', name: 'steps', component: StudentStepsStarmap, props: true },
  { path: '/adapt/:id', name: 'workshop', component: AdaptBench, props: true },
  { path: '/library', name: 'library', component: MyLibrary }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
