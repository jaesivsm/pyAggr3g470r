import React, { useState } from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";

import Tab from "@mui/material/Tab";
import Tabs from "@mui/material/Tabs";
import ImageIcon from "@mui/icons-material/Image";
import AudioIcon from "@mui/icons-material/MusicNote";
import VideoIcon from "@mui/icons-material/Movie";
import YoutubeIcon from "@mui/icons-material/YouTube";

import Article from "./Article";
import {articleTypes, TypedContents} from "./TypedContents";
import ProcessedContent from "./ProcessedContent";
import makeStyles from "./style";
import ClusterIcon from "../../../components/ClusterIcon";
import jarrIcon from "../../../components/JarrIcon.gif";

function mapStateToProps(state) {
  return { icons: state.feeds.icons,
           articles: state.clusters.loadedCluster.articles,
           contents: state.clusters.loadedCluster.contents,
  };
}
const proccessedContentTitle = "proccessed content";

function Articles({ articles, icons, contents }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const classes = makeStyles();
  const hasProcessedContent = !!contents && contents.length > 0;
  const allArticlesAreTyped = articles.reduce(
    (allTyped, art) => !!(allTyped && articleTypes.includes(art["article_type"])), true);
  // if no content, and no special type, returning simple article
  if (articles.length === 1 && !allArticlesAreTyped && !hasProcessedContent) {
    return <Article article={articles[0]} />;
  }

  let tabs = [];
  let pages = [];
  let index = 0;
  let typedArticles;
  let icon;
  const pushProcessedContent = (content) => {
    if (content.type === "youtube") {
      icon = <YoutubeIcon />;
    } else {
      icon = <img src={jarrIcon}
                  alt={proccessedContentTitle}
                  title={proccessedContentTitle} />;
    }
    tabs.push(<Tab key={`t-${index}`} value={index} icon={icon}
                   className={classes.tabs} aria-controls={`a-${index}`} />);
    pages.push(<ProcessedContent key={`pc-${index}`} content={content}
                                 hidden={index !== currentIndex} />);
    index += 1;
  }
  const pushTypedArticles = (type) => {
    typedArticles = articles.filter((article) => article.article_type === type)
          .sort((a1, a2) => (a1.order_in_cluster - a2.order_in_cluster));
    if (type === "image") {
      icon = <ImageIcon />;
    } else if (type === "audio") {
      icon = <AudioIcon />;
    } else if (type === "video") {
      icon = <VideoIcon />;
    }
    if (typedArticles.length !== 0) {
      tabs.push(<Tab key={`ta-${type}`} value={index} icon={icon}
                     className={classes.tabs} aria-controls={`a-${index}`} />);
      pages.push(<TypedContents key={`pc-${index}`} type={type}
                                articles={typedArticles}
                                hidden={index !== currentIndex} />);
      index += 1;
    }
  }
  const pushClassicArticle = (article) => {
    tabs.push(
      <Tab key={`t-${article.id}`} className={classes.tabs}
           icon={<ClusterIcon iconUrl={icons[article["feed_id"]]} />}
           value={index} aria-controls={`a-${index}`} />);
    pages.push(
      <Article key={`a-${article.id}-${index !== currentIndex ? "h" : ""}`}
               article={article} index={index} aria-labelledby={`t-${index}`}
               forceShowTitle={true} hidden={index !== currentIndex} />);
    index += 1;
  }

  if (hasProcessedContent) {
    contents.forEach(pushProcessedContent);
  }
  // if all articles are typed, pushing typed content formatter first
  if(allArticlesAreTyped) {
    articleTypes.forEach(pushTypedArticles);
    articles.forEach(pushClassicArticle);
  } else {
    // else pushing classic articles, then formatted typed, then typed
    articles.filter(
        (article) => (!articleTypes.includes(article["article_type"]))
    ).forEach(pushClassicArticle);
    articleTypes.forEach(pushTypedArticles);
    articles.filter(
        (article) => (articleTypes.includes(article["article_type"]))
    ).forEach(pushClassicArticle);
  }
  return (
    <>
      <Tabs indicatorColor="primary" textColor="primary"
        variant="scrollable" scrollButtons="auto"
        value={currentIndex}
        onChange={(e, v) => setCurrentIndex(v)}>
        {tabs}
      </Tabs>
      {pages}
    </>
  );
}
Articles.propTypes = {
  articles: PropTypes.array,
  contents: PropTypes.array
};
export default connect(mapStateToProps)(Articles);
