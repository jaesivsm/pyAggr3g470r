import React from "react";
import PropTypes from "prop-types";
import { createSelector } from "reselect";
import { connect, useDispatch } from "react-redux";
// material
import TextField from "@mui/material/TextField";
// jarr
import style from "./style";
import { editLoadedObj } from "../../slice";

const getValue = (state, props) =>
  state.edit.loadedObj[props.name] ? state.edit.loadedObj[props.name] : "";

const makeGetValue = () => createSelector([ getValue ], (value) => value);

const makeMapStateToProps = () => {
  const madeGetValue = makeGetValue();
  return (state, props) => ({ value: madeGetValue(state, props) });
};

const StateTextInput = ({ label, name, required, disabled, value }) => {
  const dispatch = useDispatch();
  return (
    <TextField required={!!required} disabled={!!disabled} variant="outlined"
               label={label} name={name}
               value={value}
               onChange={(e) => dispatch(editLoadedObj({ key: name, value: e.target.value }))}
               className={style().editPanelInput}
    />
  );
};

StateTextInput.propTypes = {
  label: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  required: PropTypes.bool,
  disabled: PropTypes.bool,
};

export default connect(makeMapStateToProps)(StateTextInput);
