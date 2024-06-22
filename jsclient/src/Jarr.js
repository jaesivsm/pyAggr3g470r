import React from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { BrowserRouter } from "react-router-dom";

import CssBaseline from "@mui/material/CssBaseline";
import { ThemeProvider } from "@mui/material/styles";

import {jarrTheme, jarrLoginTheme} from "./Jarr.theme";
import useStyles from "./Jarr.styles.js";
import NoAuth from "./features/noauth/NoAuth";
import TopMenu from "./features/topmenu/TopMenu";
import FeedList from "./features/feedlist/FeedList";
import EditPanel from "./features/editpanel/EditPanel";
import ClusterList from "./features/clusterlist/ClusterList";

function mapStateToProps(state) {
  return { isLogged: !!state.auth.accessToken, };
}

function Jarr({ isLogged, isLeftMenuOpen }) {
  const classes = useStyles();
  if (!isLogged) {
    return (
      <BrowserRouter>
        <ThemeProvider theme={jarrLoginTheme}>
          <div className={classes.root}>
            <CssBaseline />
            <NoAuth />
          </div>
        </ThemeProvider>
      </BrowserRouter>
    );
  }
  return (
    <ThemeProvider theme={jarrTheme}>
      <div className={classes.root}>
        <CssBaseline />
        <TopMenu />
        <FeedList />
        <ClusterList />
        <EditPanel />
      </div>
    </ThemeProvider>
  );
}

Jarr.propTypes = {
  isLogged: PropTypes.bool.isRequired,
};

export default connect(mapStateToProps)(Jarr);
