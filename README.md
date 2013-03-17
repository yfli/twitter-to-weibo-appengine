同步twitter到新浪微博
====================

部署在Google Appengine上，自动同步twitter到新浪微博，自动转换短链接以防止被屏蔽。

安装
---

下载本项目代码。使用git或直接下载[zip包](https://github.com/yfli/twitter-to-weibo-appengine/zipball/gtalkbot_br)

安装步骤:

* 申请一个Twitter API https://dev.twitter.com/, Callback URL为 http://'youappid'.appspot.com/oauth/callback. 更改myid.py中的CONSUMER_KEY, CONSUMER_SECRET及CALLBACK值
* 上传代码到你的appengine
* 用浏览器访问http://yourappid.appspot.com/ ,按指示操作
* Done

部署
---

更改app.yaml中的application id，上传到Google App Engine上。

部署到Google App Engine可参看下面两个教程。

* [Google App Engine 入门:上传应用程序](http://blog.xuming.net/2008/05/google-app-engine-toturial-9.html)
* [Google App Engine 6步上手教程](http://www.cnblogs.com/2011sydney/archive/2009/07/23/1529637.html)


示例
---

调试用App [http://urfatu-tw-weibo.appspot.com](http://urfatu-tw-weibo.appspot.com)

一个Lady Gaga的同步。Lady Gaga [twitter](https://twitter.com/ladygaga), 
Lady Gaga [微博](http://weibo.com/u/2841791740)

License
-------
[GPLv3][gplv3]

参考
----
本项目参考/使用了以下项目

* http://code.google.com/p/twitter-feed/
* http://atlee.ca/software/poster/
* http://code.google.com/p/twitter2weiboviagtalk/

联系
----

* [yfli](https://twitter.com/yfli)@twitter
* [warehou](http://www.weibo.com/u/1410749162)@微博

Changelog
---------

- ver 1.0 2013/3/20
 
    Major release. No need to deploy app for yourself, but use App setup by others.  
    No need to change twitter or weibo id in code. Directly binding gtalk on webpage.
    Use gtalk bot to sync. Made a mistake that thought gtalk was removed from sina while it is still available.
    Tiny.cc is blocked by sina since 3/14, change to another short url

- ver 0.4 2013/1/20

    Add Twitter OAuth for account
    Fallback to App login for weibo, as Weibo disabled gtalk bot

- ver 0.29 2012/7/31

     Enmergency update. Sina blocked Basic Auth since 7/24. Use gtalk robot instead.

- ver 0.2 2012/7/17

    Support image sync

- ver 0.1 2012/4/27

    First implement.

[gplv3]: http://www.gnu.org/licenses/gpl.html
