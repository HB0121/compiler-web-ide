import 'vant/lib/index.css' // Vant 样式
import { 
  NavBar, Field, CellGroup, Button, Form, Toast, 
  Empty, Loading, Tag, Icon, Tabbar, TabbarItem 
} from 'vant'

// 导出一个函数，专门用来挂载这些组件
export function setupVant(app) {
  app.use(NavBar)
     .use(Field)
     .use(CellGroup)
     .use(Button)
     .use(Form)
     .use(Toast)
     .use(Empty)
     .use(Loading)
     .use(Tag)
     .use(Icon)
     .use(Tabbar)
     .use(TabbarItem)
}