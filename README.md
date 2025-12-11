# MdRepo
使用[ Shields.io](https://shields.io/)服务，生成动态、静态徽章，具备一系列自定义功能。



**[shields](https://github.com/badges/shields)徽章就像下面这样**
 
  [![Stars](https://img.shields.io/github/stars/badges/shields?style=flat)](https://github.com/badges/shields/stargazers)
  [![Version](https://img.shields.io/github/v/tag/badges/shields?label=Version&style=flat)](https://github.com/badges/shields/releases)
  [![Language](https://img.shields.io/github/languages/top/badges/shields?style=flat)](https://github.com/badges/shields/search?l=JavaScript)
  [![License](https://img.shields.io/github/license/badges/shields?style=flat)](https://github.com/badges/shields/blob/master/LICENSE)
  [![Forks](https://img.shields.io/github/forks/badges/shields?style=flat)](https://github.com/badges/shields/network/members)



## 功能说明


- GitHub Token 以 json 保存在浏览器的 `localStorage` 中

- [![Version](https://img.shields.io/static/v1?label=Version&message=%E9%A2%84%E8%A7%88&color=brightgreen&style=flat)]()  ：读取 tag 标签，获取版本号

- 时间徽章
  - 首先检查仓库是否归档（Archived），归档则显示归档时间：[![Archived](https://img.shields.io/static/v1?label=Archived&message=%E9%A2%84%E8%A7%88&color=red&style=flat)]()
  - 未归档则检查发布（release），有发布则显示最新发布时间：[![Latest Release](https://img.shields.io/static/v1?label=Latest%20Release&message=%E9%A2%84%E8%A7%88&color=brightgreen&style=flat)]()
  - 没有发布，则显示最新提交（commit）时间：[![Latest Commit](https://img.shields.io/static/v1?label=Latest%20Commit&message=%E9%A2%84%E8%A7%88&color=brightgreen&style=flat)]()
 





### To Do：

- [x] 优化徽章展示逻辑
  - [x] 仓库无 release 和 tag 时显示 `latest commite` 徽章
  - [x] 处理最新版本发布时间、归档时间、最新提交时间的展示逻辑
- [x] 可选不同的徽章风格
- [x] 可调整徽章展示顺序，拖动排序或其它
- [ ] 可存储几个常用静态徽章

### 更新日志

### 2025.12.11
- 新增徽章勾选排序，排列顺序决定生成顺序

- 新增共5种徽章风格：Flat (默认扁平)、Flat Square (直角)、For-The-Badge (大号)、Plastic (3D立体)、Social (社交风格)


#### 2025.5.12
- 徽章数据获取和展示逻辑改进
   - 新增 `last commit` 徽章，优化时间徽章显示逻辑
   - 优化徽章获取逻辑，减少潜在错误
- 优化提示和反馈，改善了用户界面和交互体验
- 通过并行 API 提升性能
- 增强了代码的健壮性，提升了错误处理能力
#### 2025.4.11
- 推出正式版`MdRepo.html`


#### 2025.4.7 -- 4.10
- 增加功能，优化细节
- 经过多次迭代，发现python的GUI界面过于传统，不够美观，转HTML


#### 2025.4.6
- 只熟悉python，只能从此着手
- 使用爆火的DeepSeek以及三方集成，开干！
- 达成成就：获得`main.py`（1/1）

### 写在最后
> 此项目始于2025.4

在多次的好奇和试探后

终于搞明白了徽章是个什么东西

鉴于其高效简洁的信息表达形式

我决定大量使用

然后就有了这个工具
