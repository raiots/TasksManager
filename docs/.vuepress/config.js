// module.exports = {
//     lang: 'zh-CN',
//     title: 'TasksManager',
//     description: '超好用的任务分配管理系统',
//   }
//
import {defaultTheme, defineUserConfig} from 'vuepress'

export default defineUserConfig({
  lang: 'zh-CN',
  title: 'TasksManager',
  description: '超好用的任务分配管理系统',

  theme: defaultTheme({
    navbar: [
      {
        text: '指南',
        link: '/guide/',
      },
      {
        text: '部署',
        link: '/install/',
      }
    ],
    sidebar: "auto",
    repo: 'https://github.com/raiots/TasksManager',
    repoLabel: '✨Github',
    docsDir: 'docs',
    docsBranch: 'master',
    lastUpdatedText: "📑 最后更新",
    contributorsText: "💕 参与贡献",
    editLinkText: "🖊️ 编辑本文",
    notFound: ["👻 页面不存在"],

  }),
})

