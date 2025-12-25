import { Request, Response } from "express";
import File from "../models/file.model";
import axios from "axios"
import fs from "fs"
import FormData from "form-data";

export const uploadFile = async (req: Request, res: Response) => {
    try {

        const file = req.file
        const userId = req.user?.id;

        if (!file) {
            res.status(400).json({
                message: "No File Uploaded"
            })
            return
        }


        const formData = new FormData();
        formData.append(
            "file",
            file.buffer,
            file.originalname
        );

        // console.log(formData)

        const pythonRes = await axios.post("http://localhost:8000/analyze", formData)

        // console.log(pythonRes.data);

        const pythonData = pythonRes.data as {
            table_created?: string;
        };

        if (!pythonData.table_created) {
            return res.status(500).json({
                message: "Python service did not return table name"
            });
        }


        const tableName = (pythonRes.data as { table_created: string }).table_created;

        const fileData = new File({
            fileName: tableName,
            fileSize: file?.size,
            user: userId
        })
        await fileData.save()


        res.status(200).json({
            message: "File Uploaded Successfully",
            file: fileData
        })
        return

    } catch (error) {
        console.error(error);
        res.json({
            message: "Internal Server Error"
        })
        return
    }
}

export const getUserFile = async (req: Request, res: Response) => {
    try {
        const userId = req.user?.id;

        const userFile = await File.find({ user: userId });

        res.status(200).json({
            message: "User Files",
            file: userFile
        })

    } catch (error) {
        console.error(error);
        res.status(500).json({
            message: "Internal Server Error"
        })
        return
    }
}