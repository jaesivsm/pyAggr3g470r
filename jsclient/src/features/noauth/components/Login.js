import React from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
// material ui components
import Grid from "@mui/material/Grid";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
// jarr
import { doLogin } from "../noAuthSlice";
import makeStyles from "./style";

function mapStateToProps(state) {
  return { loginError: state.noauth.loginError,
           passwordError: state.noauth.passwordError,
  };
}

const mapDispatchToProps = (dispatch) => ({
  logIn(e) {
    e.preventDefault();
    const login = e.target.querySelector("input#jarr-login").value;
    const password = e.target.querySelector("input#jarr-password").value;
    dispatch(doLogin(null, login, password));
  },
});

function Login({ isLoading, loginError, passwordError, logIn }) {
  const classes = makeStyles();
  return (
    <form autoComplete="off" onSubmit={logIn} className={classes.loginForm}>
      <Grid item>
        <TextField required id="jarr-login" label="Login"
          className={classes.loginInput}
          disabled={isLoading}
          error={!!loginError}
          helperText={loginError}
        />
      </Grid>
      <Grid item>
        <TextField required id="jarr-password" label="Password" type="password"
          className={classes.loginInput}
          disabled={isLoading}
          error={!!passwordError}
          helperText={passwordError}
        />
      </Grid>
      <Grid item className={classes.loginButton}>
        <Button variant="contained" type="submit" color="primary">
          Login
        </Button>
      </Grid>
    </form>
  );
}

Login.propTypes = {
  isLoading: PropTypes.bool.isRequired,
  logIn: PropTypes.func.isRequired,
  loginError: PropTypes.string,
  passwordError: PropTypes.string,
};

export default connect(mapStateToProps, mapDispatchToProps)(Login);
