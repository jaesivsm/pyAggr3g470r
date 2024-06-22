import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { Switch, Route } from "react-router-dom";
// material ui components
import Grid from "@mui/material/Grid";
import IconButton from "@mui/material/IconButton";
import CircularProgress from "@mui/material/CircularProgress";
import Button from "@mui/material/Button";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
// jarr
import { apiUrl } from "../../const";
import { doLogin, responseRecieved } from "./noAuthSlice";
import makeStyles from "./components/style";
import Login from "./components/Login";
import SignUp from "./components/SignUp";
import InitPasswordRecovery from "./components/InitPasswordRecovery";
import PasswordRecovery from "./components/PasswordRecovery";
import OAuthLogin from "./components/OAuthLogin";
import jarrIcon from "../../components/JarrIcon.gif";

function mapStateToProps(state) {
  return { isLoading: state.noauth.loading,
           noAccessToken: (!state.noauth.loading && !state.auth.accessToken),
           refreshToken: state.auth.refreshToken,
           savedLogin: state.auth.login,
           savedPassword: state.auth.password,
           recovery: (state.noauth.recovery ? state.noauth.recovery.statusText : ""),
  };
}

const mapDispatchToProps = (dispatch) => ({
  hiddenLogin(refreshToken, login, password) {
    dispatch(doLogin(refreshToken, login, password));
  },
  clearStore() {
    dispatch(responseRecieved());
  },
});

function NoAuth({ isLoading, noAccessToken, savedLogin, savedPassword, refreshToken, recovery, hiddenLogin, clearStore }) {
  useEffect(() => {
    if ((refreshToken || (savedLogin && savedPassword)) && noAccessToken) {
      hiddenLogin(refreshToken, savedLogin, savedPassword);
    }
  });
  const classes = makeStyles();
  const [formType, setFormType] = useState("login");
  const closeLoginSubPage = () => {
    setFormType("login");
    clearStore();
  };

  let form;
  let header;
  let footer;
  if (formType === "login") {
    if (isLoading) {
      header = <Grid item><CircularProgress /></Grid>;
    } else {
      header = <Grid item className={classes.welcome}>
        <img className={classes.jarrIcon} src={jarrIcon} alt="Welcome to JARR!" title="Welcome to JARR!"/>
        <span>Welcome to JARR !</span>
      </Grid>;
    }
    form = <Login isLoading={isLoading} />;
    footer = (
      <>
        <Grid item className={classes.recoverButton}>
          <span onClick={(e) => setFormType("recover")}>Forgotten password ?</span>
        </Grid>
        <Grid item className={classes.googleButton}>
          <form method="get" action={`${apiUrl}/oauth/google`}>
            <Button variant="contained" type="submit" color="secondary">
              Login with Google
            </Button>
          </form>
        </Grid>
        <Grid item className={classes.signupButton}>
          <span>Don't have an account ?</span>
          <span className={classes.signupLink} variant="contained" onClick={(e) => setFormType("signup")}>Sign up</span>
        </Grid>
      </>
    );
  } else if (formType === "signup") {
    form = <SignUp isLoading={isLoading} />;
    header = (
      <Grid item className={classes.headerButton}>
         <IconButton onClick={closeLoginSubPage}>
           <ArrowBackIcon />
         </IconButton>
         {isLoading ? <CircularProgress /> : <span>Sign Up !</span>}
       </Grid>
    );
  } else if (formType === "recover") {
    form = <InitPasswordRecovery />;
    header = (
      <Grid item className={classes.headerButton}>
         <IconButton onClick={closeLoginSubPage}>
           <ArrowBackIcon />
         </IconButton>
         {isLoading ? <CircularProgress /> : <span>Password recovery</span>}
       </Grid>
    );
    if (recovery === "NO CONTENT") {
      footer = (
        <Grid item>
          An email has been sent to you, please follow instruction to
          complete recovery.
        </Grid>
      );

    } else if (recovery === "BAD REQUEST") {
      footer = (
        <Grid item>
          We could not generate you a recovery token, sorry !
        </Grid>
      );
    }
  }

  return (
    <Grid container className={classes.loginContainer} direction="column" >
      <Switch>
        <Route path="/recovery/:login/:email/:token">
          <PasswordRecovery />
          {recovery === "NOT FOUND" ? <Grid item>Could not find your user</Grid> : null}
          {recovery === "FORBIDDEN" ? <Grid item>Password NOT updated, token is expired. Please generate a new one.</Grid>: null}
        </Route>
        <Route path="/oauth/:provider">
          <OAuthLogin />
        </Route>
        <Route path="/">
          {header}
          {form}
          {footer}
        </Route>
      </Switch>
    </Grid>
  );
}

NoAuth.propTypes = {
  isLoading: PropTypes.bool.isRequired,
  noAccessToken: PropTypes.bool.isRequired,
  savedLogin: PropTypes.string,
  savedPassword: PropTypes.string,
  refreshToken: PropTypes.string,
  recovery: PropTypes.string.isRequired,
  hiddenLogin: PropTypes.func.isRequired,
};

export default connect(mapStateToProps, mapDispatchToProps)(NoAuth);
