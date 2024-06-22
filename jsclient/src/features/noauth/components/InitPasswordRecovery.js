import React, { useState } from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
// material ui components
import Grid from "@mui/material/Grid";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
// jarr
import { doInitRecovery } from "../noAuthSlice";
import makeStyles from "./style";

function mapStateToProps(state) {
  return { isLoading: state.noauth.loading };
}

const mapDispatchToProps = (dispatch) => ({
  initRecovery(e, login, email) {
    e.preventDefault();
    dispatch(doInitRecovery(login, email));
  },
});

function PasswordRecover({ isLoading, initRecovery }) {
  const classes = makeStyles();
  const [login, setLogin] = useState("");
  const [email, setEmail] = useState("");
  return (
    <form autoComplete="off" onSubmit={(e) => {
        initRecovery(e, login, email);
    }}>
      <Grid item>
        <TextField label="Login" type="text"
          className={classes.loginInput}
          disabled={isLoading}
          onChange={(e) => setLogin(e.target.value)}
        />
      </Grid>
      <Grid item>
        <TextField label="Email" type="email"
          className={classes.loginInput}
          disabled={isLoading}
          onChange={(e) => setEmail(e.target.value)}
        />
      </Grid>
      <Grid item className={classes.loginButton}>
        <Button variant="contained" type="submit" color="primary">
          Genereate Recovery Token
        </Button>
      </Grid>
    </form>
  );
}

PasswordRecover.propTypes = {
  isLoading: PropTypes.bool.isRequired,
  initRecovery: PropTypes.func.isRequired,
};

export default connect(mapStateToProps, mapDispatchToProps)(PasswordRecover);
