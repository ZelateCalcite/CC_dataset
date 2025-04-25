# CREATE DATABASE IF NOT EXISTS CC_DATASET DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE CC_DATASET;
CREATE TABLE IF NOT EXISTS user_id
(
    id       INT AUTO_INCREMENT PRIMARY KEY, -- 用户唯一标识 一个id和一个wid严格对应
    wid      CHAR(10)  NOT NULL,             -- 用户id,十位来自微博
    add_date TIMESTAMP NOT NULL,             -- 添加日期
    del_flag BOOL DEFAULT FALSE              -- 删除标识
);

CREATE TABLE IF NOT EXISTS user_meta_info
(
    id              INT,                  -- 用户唯一标识
    wid             CHAR(10) PRIMARY KEY, -- 用户id
    nickname        VARCHAR(30),          -- 用户昵称
    gender          VARCHAR(10),          -- 用户性别
    location        VARCHAR(200),         -- 用户所在地
    birthday        DATE,                 -- 用户出生日期
    description     VARCHAR(400),         -- 用户简介
    verified_reason VARCHAR(140),         -- 用户认证
    talent          VARCHAR(200),         -- 用户标签
    education       VARCHAR(200),         -- 用户学习经历
    work            VARCHAR(200),         -- 用户工作经历
    weibo_num       INT,                  -- 微博数
    following       INT,                  -- 关注数
    followers       INT,                  -- 粉丝数
    FOREIGN KEY (id) REFERENCES user_id (id)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS weibo
(
    weibo_id          VARCHAR(15) PRIMARY KEY,     -- 微博唯一标识, 标记一条微博
    wid               CHAR(10),                    -- 用户id, 这条微博发布者的id
    content           VARCHAR(5000),               -- 微博正文
    article_url       VARCHAR(200),                -- 微博中头条文章的url，若微博中不存在头条文章，则值为''
    original_pictures VARCHAR(3000),               -- 原创微博的原始图片url和转发微博转发理由中的图片url。若某条微博有多张图片，则存储多个url，以英文逗号分割；若某微博没有图片，则值为"无"
    retweet_pictures  VARCHAR(3000),               -- 被转发微博中的原始图片url。当最新微博为原创微博或者为没有图片的转发微博时，则值为"无"，否则为被转发微博的图片url。若有多张图片，则存储多个url，以英文逗号分割
    original          BOOLEAN  NOT NULL DEFAULT 1, -- 是否原创微博
    video_url         VARCHAR(300),                -- 微博的视频url
    publish_place     VARCHAR(100),                -- 微博的发布位置。如果某条微博没有位置信息，则值为"无"
    publish_time      DATETIME NOT NULL,           -- 微博的发布时间
    publish_tool      VARCHAR(30),                 -- 微博的发布工具
    up_num            INT      NOT NULL,           -- 微博获得的点赞数
    retweet_num       INT      NOT NULL,           -- 微博获得的转发数
    comment_num       INT      NOT NULL,           -- 微博获得的评论数
    FOREIGN KEY (wid) REFERENCES user_meta_info (wid)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;
