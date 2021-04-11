import React, { useState } from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";

import Tab from "@material-ui/core/Tab";
import Tabs from "@material-ui/core/Tabs";

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

  let tabs = [];
  let pages = [];
  let index = 0;
  let typedArticles;

  // if no content, and no special type, returning simple article
  if (articles.length === 1 && !(articles[0].article_type in articleTypes) && !contents) {
    return <Article article={articles[0]} hidden={false} />;
  }
  if (contents.length !== 0) {
    contents.forEach((content) => {
      tabs.push(
        <Tab key={`t-${index}`}
          className={classes.tabs}
          icon={<img src={jarrIcon}
                     alt={proccessedContentTitle}
                     title={proccessedContentTitle} />}
          value={index} aria-controls={`a-${index}`}
        />
      );
      pages.push(
          <ProcessedContent
            content={content}
            hidden={index === currentIndex}
          />
      );
      index += 1;
    });
  }
  articleTypes.forEach((type) => {
    typedArticles = articles.filter((article) => article.article_type === type);
    if (typedArticles.length !== 0) {
      tabs.push(
        <Tab key={`t-${index}`}
          className={classes.tabs}
          icon={<img src={jarrIcon} alt={type} title={type} />}
          value={index} aria-controls={`a-${index}`}
        />
      );
      pages.push(
        <TypedContents
          type={type} articles={typedArticles}
          hidden={index === currentIndex}
        />
      );
      index += 1;
    }
  });
  articles.forEach((article) => {
    tabs.push(
      <Tab key={`t-${index}`}
        className={classes.tabs}
        icon={<ClusterIcon iconUrl={icons[article["feed_id"]]} />}
        value={index}
        aria-controls={`a-${index}`}
      />);
    pages.push(
      <Article
        key={`a-${index}-${index !== currentIndex ? "h" : ""}`}
        id={`a-${index}`}
        article={article}
        aria-labelledby={`t-${index}`}
        index={index}
        hidden={index !== currentIndex}
      />
    );
    index += 1;
  });
  return (
    <>
      <Tabs indicatorColor="primary" textColor="primary"
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
  contents: PropTypes.arrayOf({
    type: PropTypes.string.isRequired,
    link: PropTypes.string.isRequired,
    comments: PropTypes.string,
    content: PropTypes.string
  }),
};
export default connect(mapStateToProps)(Articles);
