import React from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import Button from "@mui/material/Button";
import WarningIcon from "@mui/icons-material/Warning";
import { closePanel } from "../slice";
import doListClusters from "../../../hooks/doListClusters";
import doDeleteObj from "../../../hooks/doDeleteObj";

function mapStateToProps(state) {
  return { id: state.edit.loadedObj.id, };
}

const mapDispatchToProps = (dispatch) => ({
  deleteFunc(e, id, objType) {
    e.preventDefault();
    dispatch(doDeleteObj(id, objType));
    dispatch(doListClusters({ categoryId: "all" }));
    dispatch(closePanel());
  },
});

function DeleteButton({ id, type, deleteFunc, className }) {
  if (!id) {
    return null;
  }
  return (
    <Button variant="contained" color="default" type="submit"
        onClick={(e) => deleteFunc(e, id, type)}
        className={className}>
      <WarningIcon />
      Delete {type}
    </Button>
  );
}

DeleteButton.propTypes = {
  id: PropTypes.number,
  type: PropTypes.string.isRequired,
  deleteFunc: PropTypes.func.isRequired,
};

export default connect(mapStateToProps, mapDispatchToProps)(DeleteButton);
