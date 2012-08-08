同步twitter到新浪微博
====================

部署在Google Appengine上，自动同步twitter到新浪微博，自动转换短链接以防止被屏蔽。

从0.29版本开始使用Sina微博的gtalk bot同步，只能同步消息，无法同步图片。因Sina的oauth2分级政策
意味着小应用根本无法使用oauth2。事实上大应用基本都是用它的Xauth方法。


安装
---

首先下载本项目代码。使用git或直接下载[zip包](https://github.com/yfli/twitter-to-weibo-appengine/zipball/master)

安装需要以下几步。

* 申请一个[tiny.cc](http://tiny.cc)的帐号。从api页面 http://tiny.cc/api-docs 取得你的API Key
* 到微博聊天机器人绑定页面http://app.weibo.com/tool/imbot ，绑定gtalk聊天机器人。绑定帐号为[yourappid]@appspot.com。
注意[yourappid]为你将要使用的app engine id。新浪会告诉你聊天机器人的帐号（一般为sinat064@gmail.com的形式）和验证码。

* 编辑myid.py文件，把用户名、密码、验证码和申请到的App keys填入。

```console
     my_twitter_id=""
     my_weibo_bot=""
     my_weibo_bot_verify_code=""
     my_tinycc_login=""
     my_tinycc_apikey=""
```
* 上传代码到你的appengine
* 用浏览器访问http://yourappid.appspot.com/initialize。
* 到新浪页面http://app.weibo.com/tool/imbot 查看是否绑定成功，如不成功，重复上一步。

部署
---

更改app.yaml中的application id，上传到Google App Engine上。

部署到Google App Engine就是通常的app engine流程，可参看下面两个教程。

* [Google App Engine 入门:上传应用程序](http://blog.xuming.net/2008/05/google-app-engine-toturial-9.html)
* [Google App Engine 6步上手教程](http://www.cnblogs.com/2011sydney/archive/2009/07/23/1529637.html)


示例
---

这是我建的一个Lady Gaga的同步。Lady Gaga [twitter](https://twitter.com/ladygaga), 
Lady Gaga [微博](http://weibo.com/u/2841791740)

License
-------
[GPLv3][gplv3]

参考
----
本项目参考/使用了以下项目

* http://code.google.com/p/twitter-feed/
* http://atlee.ca/software/poster/

联系
----

* [yfli](https://twitter.com/yfli)@twitter
* [warehou](http://www.weibo.com/u/1410749162)@微博

Changelog
---------

- ver 0.29 2012/7/31

     Enmergency update. Sina blocked Basic Auth since 7/24. Use gtalk robot instead.

- ver 0.2 2012/7/17

    Support image sync

- ver 0.1 2012/4/27

    First implement.

[gplv3]: http://www.gnu.org/licenses/gpl.html
