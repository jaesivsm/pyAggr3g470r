import React from "react";
import PropTypes from "prop-types";
import Typography from "@mui/material/Typography";

import makeStyles from "./style";

export const articleTypes = ["image", "audio", "video"];

export function TypedContents({ type, articles, hidden }) {
  const classes = makeStyles();
  if (articles.length === 0) { return ; }
  let processedUrls = [];
  return (
    <div hidden={!!hidden} className={classes.article}>
      {articles.filter(
          (article) => {
            if (processedUrls.includes(article.link)) {
              return false;
            }
            processedUrls.push(article.link);
            return true;
          }).map((article) => {
        let media;
        if (type === "image") {
          media = (<img key={`image-${article.id}`}
                        src={article.link}
                        alt={article.title} title={article.title} />);
        } else if (type === "audio") {
          media = (<audio controls key={`audio-${article.id}`}>
                     <source src={article.link} />
                   </audio>);
          if(article.title) {
            media = (<>
                       <Typography variant="h6" key={`title-${article.id}`}>
                          {article.title}
                       </Typography>
                       {media}
                     </>);
          }
        } else if (type === "video") {
          media = (<video controls loop key={`video-${article.id}`}>
                     <source src={article.link} />
                   </video>);
          if(article.title) {
            media = (<>
                       <Typography variant="h6" key={`title-${article.id}`}>
                          {article.title}
                       </Typography>
                       {media}
                     </>);
          }
        }
        return media;
      })}
    </div>);
}

TypedContents.propTypes = {
  type: PropTypes.string.isRequired,
  articles: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.number.isRequired,
    title: PropTypes.string,
    link: PropTypes.string.isRequired,
    "article_type": PropTypes.string.isRequired})),
  hidden: PropTypes.bool.isRequired,
};
