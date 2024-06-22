import React from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
// material components
import Button from "@mui/material/Button";
import FormControl from "@mui/material/FormControl";
// jarr
import ClusterSettings from "../common/ClusterSettings";
import DeleteButton from "../common/DeleteButton";
import StateTextInput from "../common/StateTextInput";

import { closePanel } from "../slice";
import editPanelStyle from "../editPanelStyle";
import doCreateObj from "../../../hooks/doCreateObj";
import doEditObj from "../../../hooks/doEditObj";

const mapDispatchToProps = (dispatch) => ({
  commit(e, job) {
    e.preventDefault();
    if (job === "edit") {
      dispatch(doEditObj("category"));
    } else {
      dispatch(doCreateObj("category"));
    }
    dispatch(closePanel());
  },
});

function mapStateToProps(state) {
  return { catId: state.edit.loadedObj.id };
}

function AddEditCategory({ job, catId, commit }) {
  const classes = editPanelStyle();

  return (
    <form onSubmit={(e) => commit(e, job)}>
    <FormControl component="fieldset">
      <StateTextInput label="Category name" name="name" />
      <ClusterSettings level="category" />
      <div className={classes.editPanelButtons}>
        <Button className={classes.editPanelBtn} variant="contained" color="primary" type="submit">
          {job === "add" ? "Create" : "Edit"} Category
        </Button>
        <DeleteButton type="category" className={classes.deletePanelBtn} />
      </div>
    </FormControl>
    </form>
  );
}

AddEditCategory.propTypes = {
  job: PropTypes.string.isRequired,
  catId: PropTypes.number,
  commit: PropTypes.func.isRequired,
};

export default connect(mapStateToProps, mapDispatchToProps)(AddEditCategory);
