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
    id                VARCHAR(15) PRIMARY KEY,     -- 微博唯一标识, 标记一条微博
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

CREATE TABLE IF NOT EXISTS tweet_id
(
    id           INT AUTO_INCREMENT, -- 数据库唯一标识
    tweet_id     VARCHAR(20) UNIQUE, -- 一条推特的唯一id
    add_date     TIMESTAMP NOT NULL, -- 添加日期
    del_flag     BOOL DEFAULT FALSE, -- 删除标识
    fetched_flag BOOL DEFAULT FALSE, -- 爬取标识
    PRIMARY KEY (id)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS tweet
(
    tweet_id                    VARCHAR(20) UNIQUE, -- 一条推特的唯一id
    FOREIGN KEY (tweet_id) REFERENCES tweet_id (tweet_id),
    add_date                    TIMESTAMP NOT NULL, -- 添加日期
    del_flag                    BOOL DEFAULT FALSE, -- 删除标识
    user_id                     VARCHAR(20),        -- 用户id
    in_reply_to                 VARCHAR(20),        -- 回复的推特id
    created_at                  TIMESTAMP,          -- 发表日期
    text                        VARCHAR(5000),      -- 推特内容
    full_text                   VARCHAR(5000),      -- 推特全文
    lang                        VARCHAR(20),
    /*
    special language tags
    lang:und – undefined language.
    lang:qam – for tweets with mentions only (works for tweets since 2022-06-14).
    lang:qct – for tweets with cashtags only (works for tweets since 2022-06-14).
    lang:qht – for tweets with hashtags only (works for tweets since 2022-06-14).
    lang:qme – for tweets with media links only (works for tweets since 2022-06-14).
    lang:qst – for tweets with very short text (works for tweets since 2022-06-14).
    lang:zxx – for tweets with either media or Twitter Card only, without any additional text
    (works for tweets since 2022-06-14`.
    */
    possibly_sensitive          BOOL,               -- 敏感内容
    possibly_sensitive_editable BOOL,
    has_media                   BOOL,               -- 是否包含媒体内容
    reply_count                 INT,                -- 回复数量
    favorite_count              INT,                -- 喜欢数量
    favorited                   BOOL,               -- 是否喜欢
    retweet_count               INT,                -- retweet数量
    bookmark_count              INT,                -- bookmark数量
    bookmarked                  BOOL,               -- 是否bookmark
    editable_until_msecs        VARCHAR(20),        -- 未知字段
    is_translatable             BOOL,               -- 是否可以翻译
    is_edit_eligible            BOOL,
    edits_remaining             VARCHAR(10),
    view_count                  VARCHAR(15),        -- 浏览人数
    view_count_state            VARCHAR(30),        -- 浏览人数状态
    is_quote_status             BOOL,               -- 该条推特是否为quote
    quote_count                 INT,                -- quote数量
    quote                       VARCHAR(20),        -- 如果是quote 这条推特指向的推特id
#     retweeted_tweet             VARCHAR(2000),
#     urls                        VARCHAR(2000),
    hashtags                    VARCHAR(5000),      -- 标签
#     has_community_notes         VARCHAR(20),
#     community_note              VARCHAR(200),
#     thumbnail_url               VARCHAR(2000),
#     thumbnail_title             VARCHAR(200),
    has_card                    BOOL
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS tweet_media
(
    id         VARCHAR(20) PRIMARY KEY, -- 媒体的唯一标识
    media_type INT,                     -- 0 photo 1 video 2 animated_gif
    media_url  VARCHAR(1000),           -- 媒体下载链接 video animated_gif类型为封面图
    url        VARCHAR(200),            -- 推文短链接
    tweet_id   VARCHAR(20)              -- 媒体关联的推特id
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS tweet_user
(
    id               VARCHAR(20) PRIMARY KEY, -- 用户的唯一标识
    add_date         TIMESTAMP NOT NULL,      -- 添加日期
    del_flag         BOOL DEFAULT FALSE,      -- 删除标识
    name             VARCHAR(100),            -- 用户名称
    created_at       TIMESTAMP,               -- 创建日期
    followers_count  INT,                     -- 粉丝数
    following_count  INT,                     -- 关注数
    favourites_count INT,                     -- 点赞数
    screen_name      VARCHAR(100),            -- 显示名称
    description      VARCHAR(1000),           -- 描述
    location         VARCHAR(200)             -- 地址
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS weibo_pre_annotation
(
    id            INT AUTO_INCREMENT PRIMARY KEY, -- 标注的唯一标识
    add_date      TIMESTAMP NOT NULL,             -- 添加日期
    del_flag      BOOL          DEFAULT FALSE,    -- 删除标识
    weibo_id      VARCHAR(15),                    -- 用户名称
    model         INT,                            -- 0 BERT 1 Qwen3-1.7B
    annotation    VARCHAR(8000),                  -- 标注结果 JSON存储的数组
    think         VARCHAR(2000) DEFAULT NULL,     -- CoT文本
    import_status INT,                            -- 导入到Label-Studio的状态 0 未导入 1 已导入 2 导入后删除
    FOREIGN KEY (weibo_id) REFERENCES weibo (id)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;

# ALTER TABLE weibo_pre_annotation ADD UNIQUE (weibo_id);
ALTER TABLE weibo_pre_annotation
    ADD import_status INT DEFAULT 0;