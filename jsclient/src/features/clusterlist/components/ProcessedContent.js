import React from "react";
import PropTypes from "prop-types";
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";
import Divider from "@mui/material/Divider";

import makeStyles from "./style";

function ProcessedContent({ content, hidden }) {
  const classes = makeStyles();
  let title, titleDivider, link, comments, linksDivider, body;
  if (content.type === "fetched") {
    if (content.title) {
      title = (<Typography variant="h6">{content.title}</Typography>);
      titleDivider = <Divider />;
    }
    if (content.comments) {
      comments = (
        <p>
          <span>Comments</span>
          <Link color="secondary" target="_blank" href={content.comments}>
            {content.comments}
          </Link>
        </p>
      );
    }
    link = (
      <p>
        <span>Link</span>
        <Link color="secondary" target="_blank" href={content.link}>
          {content.link}
        </Link>
      </p>
    );
    body = (
      <Typography className={classes.articleInner}
          dangerouslySetInnerHTML={{__html: content.content}} />
    );
    linksDivider = <Divider />;
  } else if (content.type === "youtube") {
    body = (
      <Typography className={classes.videoContainer}>
        <iframe key="jarr-proccessed-content"
          title="JARR processed Player"
          id="ytplayer"
          type="text/html"
          src={`https://www.youtube-nocookie.com/embed/${content.link}`}
          frameBorder="0"
        />
      </Typography>
    );
  }
  return (
    <div hidden={hidden} className={classes.article}>
      {title}
      {titleDivider}
      {link}
      {comments}
      {linksDivider}
      {body}
    </div>
  );
}

ProcessedContent.propTypes = {
  content: PropTypes.shape({
    type: PropTypes.string.isRequired,
    link: PropTypes.string.isRequired,
    content: PropTypes.string,
    comments: PropTypes.string
  }),
  hidden: PropTypes.bool.isRequired,
};

export default ProcessedContent;
