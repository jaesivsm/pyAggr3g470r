import { Theme, createStyles } from "@mui/material/styles";
import { makeStyles } from "@mui/styles";

export default makeStyles((theme: Theme) =>
  createStyles({
    welcome: {
      color: "rgba(0, 0, 0, 0.6)",
      fontSize: 16
    },
    jarrIcon: {
      position: "relative",
      top: 2,
      right: 10
    },
    loginContainer: {
      alignItems: "center",
      background: "#ffffff",
      borderRadius: "1px",
      boxShadow: "grey 0px 0px 10px",
      padding: "15px 30px 10px",
      position: "absolute",
      top: "50%",
      left: "50%",
      transform: "translate(-50%, -50%)",
      height: "auto",
      width: 350,
      [theme.breakpoints.down("xs")]: {
          top: 25,
          marginBottom: 20,
          transform: "translateX(-50%)",
          width: "calc(100% - 50px)",
      },
      "& .MuiGrid-item": {
        padding: theme.spacing(1),
      },
      "& hr": {
        width: 200,
        height: 2,
        marginTop: theme.spacing(1),
        marginBottom: theme.spacing(1),
      },
    },
    loginForm: {
      width: "100%",
    },
    loginButton: {
      textAlign: "center",
      marginTop: "45px !important",
      "& button": {
        color: "#fff",
        boxShadow: "none",
        borderRadius: 0,
        width: "100%",
      },
      "& div": {
        marginBottom: theme.spacing(2),
      },
    },
    loginInput: {
      width: "100%",
    },
    signupButton: {
      color: "rgba(0, 0, 0, 0.6)",
      marginTop: 20
    },
    signupLink: {
      cursor: "pointer",
      textDecoration: "underline",
      marginLeft: 5
    },
    recoverButton: {
      color: "rgba(0, 0, 0, 0.6)",
      cursor: "pointer",
      textDecoration: "underline",
      textAlign: "right",
      position: "relative",
      top: -100,
      width: "100%",
    },
    googleButton : {
      marginTop: -35,
      width: "100%",
      "& button": {
        backgroundColor: "#dc4e41",
        boxShadow: "none",
        borderRadius: 0,
        width: "100%",
      },
      "& button:hover": {
        backgroundColor: "#dc4e41",
        opacity: 0.9
      },
    },
    passwordGridInput: {
      justifyContent: "space-between",
      display: "flex",
    },
    headerButton: {
      marginLeft: -48
    }
  })
);
