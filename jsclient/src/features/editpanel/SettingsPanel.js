import React, { useState } from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
// material component
import FormControlLabel from "@mui/material/FormControlLabel";
import Button from "@mui/material/Button";
import Switch from "@mui/material/Switch";
import FormControl from "@mui/material/FormControl";
import TextField from "@mui/material/TextField";
// jarr
import StateTextInput from "./common/StateTextInput";
import ClusterSettings from "./common/ClusterSettings";
import { closePanel, editLoadedObj } from "./slice";
import doEditObj from "../../hooks/doEditObj";
import editPanelStyle from "./editPanelStyle";

const mapDispatchToProps = (dispatch) => ({
  commit(e) {
    e.preventDefault();
    dispatch(doEditObj("user"));
    dispatch(closePanel());
  },
  editPassword(password, passwordConf) {
    if (password === passwordConf) {
      dispatch(editLoadedObj({ key: "password", value: password}));
    }
  },
});

function SettingsPanel({ editPassword, commit }) {
  const [pwdVal, setPwd] = useState("");
  const [pwdConfirm, setPwdConfirm] = useState("");
  const [showPasswd, setShowPasswd] = useState(false);
  const classes = editPanelStyle();
  return (
    <form onSubmit={(e) => commit(e)}>
    <FormControl component="fieldset">
      {["login", "email", "timezone"].map((key) => (
          <StateTextInput key={key} label={key} name={key}
            disabled={key === "login"} />
       ))}
      <ClusterSettings level="user" />
      <TextField label="Password" variant="outlined"
        className={classes.editPanelInput}
        value={pwdVal}
        error={pwdConfirm !== pwdVal}
        type={showPasswd ? "text" : "password"}
        onChange={(e) => {
          editPassword(e.target.value, pwdConfirm);
          setPwd(e.target.value);
        }} />
      <TextField label="Password confirmation" variant="outlined"
        className={classes.editPanelInput}
        value={pwdConfirm}
        error={pwdConfirm !== pwdVal}
        type={showPasswd ? "text" : "password"}
        onChange={(e) => {
          editPassword(pwdVal, e.target.value);
          setPwdConfirm(e.target.value);
        }} />
      <FormControlLabel control={<Switch
        checked={showPasswd}
        onChange={() => setShowPasswd(!showPasswd)}
        color="primary"
      />} label="Show password" />
      <Button variant="contained" color="primary" type="submit"
         className={classes.editPanelBtn}>
        Edit settings
      </Button>
    </FormControl>
    </form>
  );
}

SettingsPanel.propTypes = {
  commit: PropTypes.func.isRequired,
  editPassword: PropTypes.func.isRequired,
};

export default connect(null, mapDispatchToProps)(SettingsPanel);
