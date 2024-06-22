import React, { useState } from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
// material ui
import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import TextField from "@mui/material/TextField";
import IconButton from "@mui/material/IconButton";
import FormControl from "@mui/material/FormControl";
import HelpIcon from "@mui/icons-material/Help";
// jarr
import editPanelStyle from "../editPanelStyle";
import doBuildFeed from "../../../hooks/doBuildFeed";

const mapDispatchToProps = (dispatch) => ({
  doBuildFeed(e, feedUrl) {
    e.preventDefault();
    dispatch(doBuildFeed(feedUrl));
  },
});


const BuildFeed = ({ isLoading, doBuildFeed }) => {
  const [feedUrl, setFeedUrl] = useState(null);
  const classes = editPanelStyle();
  const [showHelp, setShowHelp] = useState(false);
  let help;
  if(showHelp) {
    help = (
      <Alert>
        <p>Enter any kind of URL, site or feed, and we&apos;ll try to construct a feed from it.</p>
        <p>You may try, for example with any subreddit, your favorite news outlet or a blog you fancy.</p>
        <p>If multiple feed are available, we&apos;ll propose them to you in the next panel. You&apos;ll also be able to choose the type of integration for that particular feed.</p>
      </Alert>
    );
  }
  return (
    <form onSubmit={(e) => doBuildFeed(e, feedUrl) }>
    <FormControl component="fieldset">
      <TextField required autoFocus label="Feed Url" variant="outlined"
        helperText="Site or feed url, we'll sort it out from there ;)"
        disabled={isLoading}
        onChange={(e) => (setFeedUrl(e.target.value))}
        className={classes.editPanelInput}
      />
      <IconButton onClick={() => setShowHelp(!showHelp)}
                  className={classes.buildFeedHelpButton}>
        <HelpIcon />
      </IconButton>
      {help}
      <Button disabled={isLoading}
          variant="contained" color="primary" type="submit">
        Build feed from URL
      </Button>
    </FormControl>
    </form>
  );
};

BuildFeed.propTypes = {
  doBuildFeed: PropTypes.func.isRequired,
};

export default connect(null, mapDispatchToProps)(BuildFeed);
